from oscar.core.loading import get_model
from oscarapi.utils.loading import get_api_class
from oscarapicheckout.views import CheckoutView
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.api_set.serializers.basket import WncBasketSerializer as BasketSerializer
from apps.api_set.serializers.orders import OrderDetailSerializer
from django_oscar_buy_now_api.basket_manager import generate_buy_now_basket
from ..serializers import CheckoutSerializer
from oscarapicheckout.signals import order_placed
from oscarapicheckout.states import DECLINED, CONSUMED
from oscarapicheckout import utils


AddProductSerializer = get_api_class('serializers.product', 'AddProductSerializer')
Basket = get_model("basket", "Basket")  # noqa


class BuyNowCreateBasket(APIView):
    """
    Genrate a Buy Now Basket.

    POST(url, quantity)
    {
        "url": "http://testserver.org/oscarapi/products/209/",
        "quantity": 6
    }

    If you've got some options to configure for the product to add to the
    basket, you should pass the optional ``options`` property:
    {
        "url": "http://testserver.org/oscarapi/products/209/",
        "quantity": 6,
        "options": [
            {
                "option": "http://testserver.org/oscarapi/options/1/",
                "value": "some value"
            },{
                "option": "http://testserver.org/oscarapi/options/1/",
                "value": "some value"
            }
        ]
    }

    Will return a basket object
    """

    serializer_class = AddProductSerializer
    basket_serializer_class = BasketSerializer
    http_method_names = ['post', 'options']

    def post(self, request, *args, **kwargs):

        input_serializer = self.serializer_class(data=request.data, context={"request": request})
        if input_serializer.is_valid():
            # GET PRODUCT QUANTITY AND OPTIONS
            sr = input_serializer.validated_data['url']
            qty = input_serializer.validated_data['quantity']
            options = input_serializer.validated_data.get('options', [])

            # GENERATE BASKET
            basket = generate_buy_now_basket(request, product=sr, quantity=qty, options=options)

            # SERIALIZE
            basket_serializer = self.basket_serializer_class(basket, context={'request': request})
            return Response({**basket_serializer.data}, status=status.HTTP_201_CREATED)
        else:
            return Response(input_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BuyNowUpdateQuantity(APIView):
    serializer_class = AddProductSerializer
    basket_serializer_class = BasketSerializer
    http_method_names = ['post', 'options']
    kwargs_basket_key = 'basket'

    def post(self, request, *args, **kwargs):
        input_serializer = self.serializer_class(data=request.data, context={"request": request})
        if input_serializer.is_valid():
            # GET PRODUCT QUANTITY AND OPTIONS
            sr = input_serializer.validated_data['url']
            qty = input_serializer.validated_data['quantity']
            options = input_serializer.validated_data.get('options', [])

            basket_id = kwargs.get(self.kwargs_basket_key)
            if not basket_id:
                return Response({"basket": "No Basket found"}, status.HTTP_406_NOT_ACCEPTABLE)

            basket = get_object_or_404(Basket, pk=basket_id)

            # GENERATE BASKET
            basket.add_product(sr, qty, options)

            # SERIALIZE
            basket_serializer = self.basket_serializer_class(basket, context={'request': request})
            return Response({**basket_serializer.data}, status=status.HTTP_201_CREATED)
        else:
            return Response(input_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BuyNowCheckoutBasket(CheckoutView):
    """
    Checkout and use a WFRS account as payment.

    POST(basket, shipping_address, wfrs_source_account,
         [total, shipping_method_code, shipping_charge, billing_address]):
    {
        "basket": "/api/baskets/1/",
        "guest_email": "foo@example.com",
        "total": "100.0",
        "shipping_charge": {
            "currency": "EUR",
            "excl_tax": "10.0",
            "tax": "0.6"
        },
        "shipping_method_code": "no-shipping-required",
        "shipping_address": {
            "country": "/api/countries/NL/",
            "first_name": "Henk",
            "last_name": "Van den Heuvel",
            "line1": "Roemerlaan 44",
            "line2": "",
            "line3": "",
            "line4": "Kroekingen",
            "notes": "Niet STUK MAKEN OK!!!!",
            "phone_number": "+31 26 370 4887",
            "postcode": "7777KK",
            "state": "Gerendrecht",
            "title": "Mr"
        },
        "payment": {
            "cash": {
                "amount": "100.00"
            }
        }
    }

    Returns the order object.
    """
    http_method_names = ['get', 'post', 'options']
    serializer_class = CheckoutSerializer
    order_serializer_class = OrderDetailSerializer
    kwargs_basket_key = 'basket'

    def post(self, request, format=None, **kwargs):
        basket_id = kwargs.get(self.kwargs_basket_key)
        if not basket_id:
            return Response({"basket": "No Basket found"}, status.HTTP_406_NOT_ACCEPTABLE)

        # Wipe out any previous state data
        utils.clear_consumed_payment_method_states(request)

        # Validate the input
        c_ser = self.get_serializer(data=request.data)

        if not c_ser.is_valid():
            return Response(c_ser.errors, status.HTTP_406_NOT_ACCEPTABLE)

        # Freeze basket
        basket = c_ser.validated_data.get('basket')
        basket.freeze()

        # Save Order
        order = c_ser.save()

        # Send order_placed signal
        order_placed.send(sender=self, order=order, user=request.user, request=request)

        # Save payment steps into session for processing
        previous_states = utils.list_payment_method_states(request)
        new_states = self._record_payments(
            previous_states=previous_states,
            request=request,
            order=order,
            methods=c_ser.fields['payment'].methods,
            data=c_ser.validated_data['payment'])
        utils.set_payment_method_states(order, request, new_states)

        # Return order data
        o_ser = self.order_serializer_class(order, context={ 'request': request })
        return Response(o_ser.data)






import pprint

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.conf import settings
from oscarapi.permissions import IsOwner

from apps.address.models import UserAddress
from oscar.core import prices
from oscarapi.basket.operations import assign_basket_strategy
from oscarapicheckout import utils
from oscarapicheckout.serializers import OrderSerializer
from oscarapicheckout.signals import order_placed
from oscarapicheckout.states import DECLINED, CONSUMED
from oscarapicheckout.utils import CHECKOUT_ORDER_ID
from oscarapicheckout.views import CheckoutView as OscarAPICheckoutView
from rest_framework import status, serializers, generics
from rest_framework.response import Response
from rest_framework.reverse import reverse

from ..calculators import OrderTotalCalculator
from ..serializers.checkout import (
    CheckoutSerializer, UserAddressSerializer,
)
from ...basket.models import Basket
from ...shipping.repository import Repository
from ...users.models import Location
from ...api_set.serializers.basket import WncBasketSerializer
from ...basket.utils import order_to_basket


def _login_and_location_required(func):
    def _wrapper(request, *args, **kwargs):
        if request.user.is_anonymous:
            return JsonResponse({'detail': 'You have to be logged-in to create Order.'}, status=status.HTTP_400_BAD_REQUEST)
        if not request.session.get('location'):
            return JsonResponse({'detail': 'Geolocation not provided'}, status=status.HTTP_400_BAD_REQUEST)
        return func(request, *args, **kwargs)
    return _wrapper


@method_decorator(_login_and_location_required, name="dispatch")
class CheckoutView(OscarAPICheckoutView):
    __doc__ = """
    Prepare an order for checkout.

    NEW FROMAT:
    POST 
    # COD
    {
        "basket": f"https://store.demo.fegno.com/api/v1/baskets/{basket.id}/",
        "basket_id": basket.id,
        # "total": float(basket.total_incl_tax),
        "notes": "Some Notes for address as string.",
        "phone_number": "+919497270863",
        "shipping_address": (User Address ID),
        "billing_address": (User Address ID),
        "payment": cash
    }
    # Prepaid
    {
        "basket": f"https://store.demo.fegno.com/api/v1/baskets/{basket.id}/",
        "basket_id": basket.id,
        # "total": float(basket.total_incl_tax),
        "notes": "Some Notes for address as string.",
        "phone_number": "+919497270863",
        "shipping_address": (User Address ID),
        "billing_address": (User Address ID),
        "payment": "razor_pay",
        "razorpay_payment_id": "pay_A2IJ20983u498hR"
    }

    OLD DEPRICATED FORMAT
    POST(basket, shipping_address,
    [total, shipping_method_code, shipping_charge, billing_address]):
    {
        "basket":"https://store.demo.fegno.com/api/v1/baskets/8853/",
        "guest_email":"",
        "total":5413.13,
        "shipping_method_code":"free_shipping",
        "shipping_charge":{
            "excl_tax": 0.0,
            "currency": "INR",
            "incl_tax": 0.0,
            "tax": 0.0
        },
        "shipping_address":{
            "title":"Mr",
            "first_name":"JERIN",
            "last_name":"JOHN",
            "line1":"Kachirackal House",
            "line2":"Vennikulam P O",
            "line3":"Thiruvalla",
            "line4":"Thiruvalla",
            "state":"Kerala",
            "postcode":"689544",
            "phone_number":"+919446600863",
            "notes":"",
            "country":"https://store.demo.fegno.com/api/v1/countries/IN/"
        },
        "billing_address":{
            "title":"Mr",
            "first_name":"JERIN",
            "last_name":"JOHN",
            "line1":"Kachirackal House",
            "line2":"Vennikulam P O",
            "line3":"Thiruvalla",
            "line4":"Thiruvalla",
            "state":"Kerala",
            "postcode":"689544",
            "phone_number":"+919446600863",
            "notes":"",
            "country":"https://store.demo.fegno.com/api/v1/countries/IN/"
        },
        "payment":{
            "cash": {
            "enabled": true,
            "pay_balance": true
            }
        }
    }
       
    OR ANOTHER PAYMENT OBJECT (Pay 10000.0 With razorpay and pay balance with cash.)
    "payment":{
        "cash":{
            "enabled": true,
            "pay_balance": true,
        },
        "razor_pay": {
            "enabled": true,
            "amount": "10000.00",
            "razorpay_payment_id": "pay_zk324df2...."
        }
    }
    YET OR ANOTHER PAYMENT OBJECT (PAY COD.)
    "payment":{
        "cash":{
            "enabled": true,
            "pay_balance": true,
        },
        "razor_pay": {
            "enabled": false,
        }
    }
    
    API Supports multiple payments integration, though our system doesnot' well support this feature. (futurestic one.)
    returns the order object.
    
    """
    serializer_class = CheckoutSerializer

    def post(self, request, format=None):
        # Wipe out any previous state data
        utils.clear_consumed_payment_method_states(request)
        user = request.user if request.user and request.user.is_authenticated else None
        # Validate the input
        data = request.data.copy()
        basket = Basket.open.filter(pk=data.get('basket_id', 0)).filter(owner=user).first()
        if basket is None:
            return Response({'errors': {"basket": [
                "Basket does not Exists"
            ]}}, status=status.HTTP_406_NOT_ACCEPTABLE)
        basket = assign_basket_strategy(basket, request)
        shipping_address = UserAddress.objects.filter(user=user, pk=data.get('shipping_address')).first()
        if shipping_address is None:
            return Response({'errors': {"shipping_address": [
                "User Address for shipping does not exists"
            ]}}, status=status.HTTP_406_NOT_ACCEPTABLE)
        billing_address = UserAddress.objects.filter(user=user, pk=data.get('billing_address')).first()
        if billing_address is None:
            return Response({'errors': {"billing_address": [
                "User Address for billing does not exists"
            ]}}, status=status.HTTP_406_NOT_ACCEPTABLE)
        try:
            ship = Repository().get_default_shipping_method(
                basket=basket, shipping_addr=shipping_address,
            )
        except serializers.ValidationError:
            return Response({'errors': {"shipping_address": [
                "User Address for billing does not exists"
            ]}}, status=status.HTTP_406_NOT_ACCEPTABLE)

        shipping_cost: prices.Price = ship.calculate(basket)
        # total_amt = float(basket.total_incl_tax + shipping_cost.incl_tax)
        total_amt = OrderTotalCalculator(request=request).calculate(basket, shipping_cost)
        sample_data = {
            "basket": request.build_absolute_uri(reverse("basket-detail", kwargs={'pk': basket.pk})),
            # "total": total_amt.incl_tax,
            "shipping_method_code": ship.code,
            "shipping_charge": {
                "excl_tax": shipping_cost.excl_tax,
                "currency": shipping_cost.currency,
                "incl_tax": shipping_cost.incl_tax,
                "tax": 0.0
            },
            "shipping_address": {
                "title": shipping_address.title,
                "first_name": shipping_address.first_name,
                "last_name": shipping_address.last_name,
                "line1": shipping_address.line1,
                "line2": shipping_address.line2,
                "line3": shipping_address.line3,
                "line4": shipping_address.line4,
                "state": shipping_address.state,
                "postcode": shipping_address.postcode,
                "phone_number": data.get('phone_number') or f"+91 {request.user.username}",
                "notes": data.get('notes'),
                "country": request.build_absolute_uri(f"/api/v1/countries/{shipping_address.country.pk}/"),
                "location": f'POINT({shipping_address.location.x} {shipping_address.location.y})' if shipping_address.location else None
            },
            "billing_address": {
                "title": shipping_address.title,
                "first_name": shipping_address.first_name,
                "last_name": shipping_address.last_name,
                "line1": shipping_address.line1,
                "line2": shipping_address.line2,
                "line3": shipping_address.line3,
                "line4": shipping_address.line4,
                "state": shipping_address.state,
                "postcode": shipping_address.postcode,
                "phone_number": data.get('phone_number') or f"+91 {request.user.username}",
                "notes": data.get('notes'),
                "country": request.build_absolute_uri(f"/api/v1/countries/{shipping_address.country.pk}/")
            },
            "payment": {
                "cash": {
                    "enabled": data.get('payment') == 'cash',
                    "amount": total_amt.incl_tax if data.get('payment') == 'cash' else 0,
                },
                "razor_pay": {
                    "enabled": data.get('payment') == 'razor_pay',
                    "amount": total_amt.incl_tax if data.get('payment') == 'razor_pay' else 0,
                    "razorpay_payment_id": data.get('razorpay_payment_id')
                }
            }
        }
        pprint.pprint(sample_data)

        c_ser = self.get_serializer(data=sample_data)
        if not c_ser.is_valid():
            return Response(c_ser.errors, status.HTTP_406_NOT_ACCEPTABLE)
        location = shipping_address.location
        if not location:
            return Response({'errors': {"non_field_errors": [
                "You have not provided your location yet."
            ]}}, status=status.HTTP_406_NOT_ACCEPTABLE)
        # Freeze basket
        basket = c_ser.validated_data.get('basket')
        basket.freeze()

        # Save Order
        order = c_ser.save()
        request.session[CHECKOUT_ORDER_ID] = order.id

        # adding location from user request to
        order.shipping_address.location = location
        order.shipping_address.save()
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

        o_ser = OrderSerializer(order, context={'request': request})

        if order.status == settings.ORDER_STATUS_PAYMENT_DECLINED:
            basket = order_to_basket(order, request=request)
            b_ser = WncBasketSerializer(basket, context={'request': request})
            return Response({
                'new_basket': b_ser.data,
                'failed_order': o_ser.data,
                'message': "Payment Declined!",
            }, status=400)

        # Return order data
        return Response(o_ser.data)

    def _record_payments(self, previous_states, request, order, methods, data):
        order_balance = [order.total_incl_tax]
        new_states = {}

        def record(method_key, method_data):
            # If a previous payment method at least partially succeeded, hasn't been consumed by an
            # order, andx` is for the same amount, recycle it. This requires that the amount hasn't changed.

            # Get the processor class for this method
            code = method_data['method_type']
            method = methods[code]

            state = None
            if method_key in previous_states:
                prev = previous_states[method_key]
                if prev.status not in (DECLINED, CONSUMED):
                    if prev.amount == method_data['amount']:
                        state = prev
                    else:
                        # Previous payment exists but we can't recycle it; void whatever already exists.
                        method.void_existing_payment(request, order, method_key, prev)

            # Previous payment method doesn't exist or can't be reused. Create it now.
            if not state:
                method_data.update()
                state = method.record_payment(request, order, method_key,  **method_data)
            # Subtract amount from pending order balance.
            order_balance[0] = order_balance[0] - state.amount
            return state

        # Loop through each method with a specified amount to charge
        data_amount_specified = {k: v for k, v in data.items() if not v['pay_balance'] and v['enabled']}
        for key, method_data in data_amount_specified.items():
            new_states[key] = record(key, method_data)

        # Change the remainder, not covered by the above methods, to the method marked with `pay_balance`
        data_pay_balance = {k: v for k, v in data.items() if v['pay_balance'] and v['enabled']}
        for key, method_data in data_pay_balance.items():
            method_data['amount'] = order_balance[0]
            new_states[key] = record(key, method_data)

        return new_states


class UserAddressDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserAddressSerializer
    permission_classes = (IsOwner,)

    def get_queryset(self):
        return UserAddress.objects.filter(user=self.request.user)



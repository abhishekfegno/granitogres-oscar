from django.conf import settings
from oscarapicheckout import utils
from oscarapicheckout.serializers import OrderSerializer
from oscarapicheckout.signals import order_placed
from oscarapicheckout.states import DECLINED, CONSUMED
from oscarapicheckout.utils import CHECKOUT_ORDER_ID
from oscarapicheckout.views import CheckoutView as OscarAPICheckoutView
from rest_framework import status
from rest_framework.response import Response

from ..serializers.checkout import (
    CheckoutSerializer,
    # OrderSerializer,
    # PaymentMethodsSerializer,
    # PaymentStateSerializer
)
from ...api_set.serializers.basket import BasketSerializer, WncBasketSerializer
from ...basket.utils import order_to_basket


class CheckoutView(OscarAPICheckoutView):
    __doc__ = """
    Prepare an order for checkout.
    
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

        # Validate the input
        c_ser = self.get_serializer(data=request.data)
        if not c_ser.is_valid():
            return Response(c_ser.errors, status.HTTP_406_NOT_ACCEPTABLE)

        # Freeze basket
        basket = c_ser.validated_data.get('basket')
        basket.freeze()

        # Save Order
        order = c_ser.save()
        request.session[CHECKOUT_ORDER_ID] = order.id

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
            # order, and is for the same amount, recycle it. This requires that the amount hasn't changed.

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
        data_amount_specified = { k: v for k, v in data.items() if not v['pay_balance'] and v['enabled']}
        for key, method_data in data_amount_specified.items():
            new_states[key] = record(key, method_data)

        # Change the remainder, not covered by the above methods, to the method marked with `pay_balance`
        data_pay_balance = {k: v for k, v in data.items() if v['pay_balance'] and v['enabled']}
        for key, method_data in data_pay_balance.items():
            method_data['amount'] = order_balance[0]
            new_states[key] = record(key, method_data)

        return new_states




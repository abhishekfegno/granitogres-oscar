from django.db.models import F
from django.utils.decorators import method_decorator
from oscarapi.basket.operations import assign_basket_strategy
from oscarapicheckout import utils
from oscarapicheckout.views import CheckoutView as OscarAPICheckoutView
from rest_framework import status
from rest_framework.response import Response

from .checkout import _login_and_location_required
from ..serializers.checkout import (
    CheckoutSerializer,
)
from ...basket.models import Basket
from ...payment import refunds


@method_decorator(_login_and_location_required, name="dispatch")
class CheckoutValidationView(OscarAPICheckoutView):
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
    order_object = None
    
    def post(self, request, format=None):
        errors_out = {
            'common_error': None,
            'has_error': False,
            'errors': {},
        }        
        
        # Wipe out any previous state data
        utils.clear_consumed_payment_method_states(request)
        user = request.user if request.user and request.user.is_authenticated else None
        # Validate the input
        data = request.data.copy()
        basket = Basket.open.filter(pk=data.get('basket_id', 0)).filter(owner=user).first()
        
        if basket is None:
            errors_out['common_error'] = "Basket does not Exists"
            errors_out['has_error'] = True
        basket = assign_basket_strategy(basket, request)
        if basket.is_empty:
            errors_out['common_error'] = "Basket is Empty!"
            errors_out['has_error'] = True
        if errors_out['has_error']:
            return Response(errors_out, status=status.HTTP_400_BAD_REQUEST)

        for line in basket.all_lines():
            result = basket.strategy.fetch_for_line(line)
            is_permitted, reason = result.availability.is_purchase_permitted(line.quantity)
            if not is_permitted:
                msg = "'%(title)s' is no longer available to buy (%(reason)s). Please adjust your basket to continue." % {
                    'title': line.product.get_title(),
                    'reason': reason,
                }
                errors_out['errors'][line.id] = {
                    'line_id': line.id,
                    'product_id': line.product_id,
                    'stockrecord_id': line.stockrecord_id,
                    'msg': msg,
                    'net_stock_level': max(0, line.stockrecord.net_stock_level),
                    'quantity': line.quantity,
                }
                errors_out['has_error'] = True
        if errors_out['has_error']:
            return Response(errors_out, status=status.HTTP_400_BAD_REQUEST)
        return Response(errors_out)

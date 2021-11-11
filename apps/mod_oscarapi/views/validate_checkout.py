from django.db.models import F
from django.utils.decorators import method_decorator
from oscarapi.basket.operations import assign_basket_strategy
from oscarapicheckout import utils
from oscarapicheckout.views import CheckoutView as OscarAPICheckoutView
from rest_framework import status, serializers
from rest_framework.response import Response

from .checkout import _login_and_location_required
from ..serializers.checkout import (
    CheckoutSerializer,
)
from ...basket.models import Basket
from ...payment import refunds


class CheckoutValidationSerializer(serializers.Serializer):
    basket_id = serializers.PrimaryKeyRelatedField(queryset=Basket.open.all()|Basket.buy_now.all())


@method_decorator(_login_and_location_required, name="dispatch")
class CheckoutValidationView(OscarAPICheckoutView):
    __doc__ = """
    Prepare an order for checkout.
    POST {
        "basket_id": basket.id,
    }
    """
    serializer_class = CheckoutValidationSerializer
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
        basket = Basket.open.filter(pk=data.get('basket_id', 0)).filter().first()
        
        if basket is None:
            errors_out['common_error'] = "Basket does not Exists"
            errors_out['has_error'] = True
        if errors_out['has_error']:
            return Response(errors_out, status=status.HTTP_406_NOT_ACCEPTABLE)
        basket = assign_basket_strategy(basket, request)
        if basket.is_empty:
            errors_out['common_error'] = "Basket is Empty!"
            errors_out['has_error'] = True
        if errors_out['has_error']:
            return Response(errors_out, status=status.HTTP_406_NOT_ACCEPTABLE)
        for line in basket.all_lines():
            result = basket.strategy.fetch_for_line(line)
            is_permitted, reason = result.availability.is_purchase_permitted(line.quantity)
            if not is_permitted:
                msg = "This item is no longer available to buy (%(reason)s). Please adjust your basket to continue." % {
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
            return Response(errors_out, status=status.HTTP_406_NOT_ACCEPTABLE)
        return Response(errors_out)

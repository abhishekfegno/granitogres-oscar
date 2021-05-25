from django.conf import settings
from rest_framework import serializers
from rest_framework.relations import HyperlinkedIdentityField

from apps.order.models import Order
from apps.utils.utils import get_statuses


class OrderListSerializer(serializers.ModelSerializer):
    url = HyperlinkedIdentityField('api-orders-detail-v2')
    is_returnable = serializers.SerializerMethodField()
    is_cancellable = serializers.SerializerMethodField()
    can_return_until = serializers.SerializerMethodField()
    is_on_the_way = serializers.SerializerMethodField()
    info = serializers.SerializerMethodField()
    __return_lines = None

    def get_return_lines(self, instance):
        if self.__return_lines is None:
            self.__return_lines = instance.lines.filter(status__in=get_statuses(112))
        return self.__return_lines
    
    def get_info(self, instance) -> dict:
        if self.get_is_on_the_way(instance):
            return {
                'type': 'info',
                'message': "On the way to your doorstep"
            }
        return_statuses = [s.status for s in self.__return_lines]
        if settings.ORDER_STATUS_RETURNED in  return_statuses:
            return {
                'type': 'warning',
                'message': "Partially returned"
            }
        elif settings.ORDER_STATUS_RETURN_APPROVED in return_statuses:
            return {
                'type': 'warning',
                'message': "Returned approved!"
            }
        elif settings.ORDER_STATUS_RETURN_REQUESTED in return_statuses:
            return {
                'type': 'warning',
                'message': "Return request waiting for approval"
            }
        return {
                'type': 'success',
                'message': ""
            }
    
    def get_is_returnable(self, instance) -> dict:
        order = instance
        if order.status in get_statuses(775):
            return {
                'status': False,
                'should_display': False,
                'reason': 'Order is on the way!'
            }
        if order.is_return_time_expired:
            return {
                'status': False,
                'should_display': True,
                'reason': 'Return Time is Over.'
            }
        line_statuses = len(self.__return_lines)
        if line_statuses:
            return {
                'status': False,
                'should_display': True,
                'reason': f'You already have initiated / processed  a return request against {line_statuses} items.'
            }
        try:
            t = str(order.max_time_to__return.strptime("%c"))
        except:
            t = f"{order.max_time_to__return}"
        return {
                'status': True,
                'should_display': False,
                'reason': f'You can return any item ' + ((
                        order.max_time_to__return
                        and ('within ' + t)
                ) or '')
            }

    def get_is_cancellable(self, instance) -> bool:
        return instance.is_cancelable

    def get_is_on_the_way(self, instance) -> bool:
        return instance.status in get_statuses(6)

    def get_can_return_until(self, instance) -> str:
        time_to_return = instance.max_time_to__return
        return time_to_return and str(time_to_return)

    basket_total_incl_tax = serializers.SerializerMethodField()

    def get_basket_total_incl_tax(self, instance):
        return instance.basket_total_incl_tax and float(instance.basket_total_incl_tax)

    total_incl_tax = serializers.SerializerMethodField()

    def get_total_incl_tax(self, instance):
        return instance.total_incl_tax and float(instance.total_incl_tax)

    shipping_incl_tax = serializers.SerializerMethodField()

    def get_shipping_incl_tax(self, instance):
        return instance.shipping_incl_tax and float(instance.shipping_incl_tax)

    total_excl_tax = serializers.SerializerMethodField()

    def get_total_excl_tax(self, instance):
        return instance.total_excl_tax and float(instance.total_excl_tax)

    class Meta:
        model = Order
        fields = (
            'id', 'number', 'currency',
            'basket_total_incl_tax',
            'shipping_incl_tax',
            'total_incl_tax', 'total_excl_tax',
            'date_delivered',
            'num_lines', 'status', 'url', 'date_placed',
            'is_returnable', 'is_cancellable', 'can_return_until', 'is_on_the_way'
        )

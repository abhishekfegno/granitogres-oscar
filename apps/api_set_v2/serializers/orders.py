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

    def get_is_returnable(self, instance) -> dict:
        order = instance
        if order.status in get_statuses(775):
            return {
                'status': False,
                'should_display': False,
                'reason': 'Order is not yet delivered!'
            }
        if order.is_return_time_expired:
            return {
                'status': False,
                'should_display': True,
                'reason': 'Return Time is Over.'
            }
        line_statuses = order.lines.filter(status__in=get_statuses(112)).count()
        if line_statuses:
            return {
                'status': False,
                'should_display': True,
                'reason': f'You already have initiated / processed  a return request against {line_statuses} items.'
            }
        return {
                'status': True,
                'should_display': False,
                'reason': f'You can return any item ' + ((
                        order.max_time_to__return
                        and ('within ' + str(order.max_time_to__return.strptime("%c")))
                ) or '')
            }

    def get_is_cancellable(self, instance) -> bool:
        return instance.is_cancelable

    def get_is_on_the_way(self, instance) -> bool:
        return instance.status in get_statuses(6)

    def get_can_return_until(self, instance) -> str:
        time_to_return = instance.max_time_to__return
        return time_to_return and str(time_to_return)

    class Meta:
        model = Order
        fields = (
            'id', 'number', 'currency', 'total_incl_tax', 'date_delivered',
            'num_lines', 'status', 'url', 'date_placed',
            'is_returnable', 'is_cancellable', 'can_return_until', 'is_on_the_way'
        )

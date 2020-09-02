from oscar.templatetags.currency_filters import currency
from rest_framework import serializers

from apps.logistics.models import DeliveryTrip


class DeliveryTripSerializer(serializers.ModelSerializer):
    orders = serializers.SerializerMethodField()
    returns = serializers.SerializerMethodField()
    cod_to_collect = serializers.SerializerMethodField()

    def get_orders(self, instance):
        return [{
            'consignment_id': consignment.id,
            'id': consignment.order.id,
            'type': 'order',
            'order_number': consignment.order.number,
            'date_placed': consignment.order.date_placed,
            'num_items': consignment.order.num_items,
            'total_incl_tax': consignment.order.total_incl_tax,
            'shipping': consignment.order.shipping_address.summary,
            'contact': str(consignment.order.shipping_address.phone_number),
            'notes': consignment.order.shipping_address.notes,
        } for consignment in instance.delivery_consignments.select_related(
            'order', 'order__shipping_address')]

    def get_returns(self, instance):
        return [{
            'consignment_return_id': cons.id,
            'id': cons.order_line.id,
            'type': 'order_item',
            'order_number': cons.order_line.order.number,
            'order_id': cons.order_line.order.id,
            'date_placed': cons.order_line.order.date_placed,
            'num_items': cons.order_line.order.num_items,
            'total_incl_tax': cons.order_line.order.total_incl_tax,
            'shipping': cons.order_line.order.shipping_address.summary,
            'contact': str(cons.order_line.order.shipping_address.phone_number),
            'notes': cons.order_line.order.shipping_address.notes,
        } for cons in instance.return_consignments.select_related(
            'order_line', 'order_line__order', 'order_line__order__shipping_address')]

    def get_cod_to_collect(self, instance):
        return {
            'via_delivery': instance.cods_to_collect,
            'via_return': instance.cods_to_return,
        }

    class Meta:
        model = DeliveryTrip
        fields = (
            'id', 'route', 'info', 'updated_at',
            'orders', 'returns', 'cod_to_collect'
        )


class DeliveryTripDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = DeliveryTrip
        fields = ('id', 'updated_at', 'orders')


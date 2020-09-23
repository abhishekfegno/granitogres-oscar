from collections import defaultdict
from decimal import Decimal

from oscar.templatetags.currency_filters import currency
from rest_framework import serializers

from apps.api_set.serializers.mixins import ProductPrimaryImageFieldMixin, ProductAttributeFieldMixin
from apps.logistics.models import DeliveryTrip, Constant
from apps.payment.refunds import RefundFacade


class DeliveryTripSerializer(serializers.ModelSerializer):
    orders = serializers.SerializerMethodField()
    returns = serializers.SerializerMethodField()
    cod_to_collect = serializers.SerializerMethodField()

    def get_orders(self, instance):
        def get_source_data(order):
            source = RefundFacade().get_sources_model_from_order(order).first()
            if source:
                return {
                    'payment_type': source.source_type.name,
                    'amount_allocated': source.amount_allocated,
                    'amount_debited': source.amount_debited,
                    'is_paid': source.source_type.code.lower() != 'cash',
                    'amount_refunded': source.amount_refunded,
                    'amount_available_for_refund': source.amount_available_for_refund,
                    'reference': source.reference,
                }
        cx = ProductPrimaryImageFieldMixin()
        cx.context = self.context
        return [{
            'consignment_id': consignment.id,
            'id': consignment.order.id,
            'type': 'order',
            'consignment_status': consignment.status,
            'source': get_source_data(consignment.order),
            'order_number': consignment.order.number,
            'order_status': consignment.order.status,
            'date_placed': consignment.order.date_placed,
            'num_items': consignment.order.num_items,
            'total_incl_tax': consignment.order.total_incl_tax,
            'refund': None,
            'shipping': consignment.order.shipping_address.summary,
            'contact': str(consignment.order.shipping_address.phone_number),
            'notes': consignment.order.shipping_address.notes,
            'lines': [{
                'product_name': line.product.name,
                'primary_image': cx.get_primary_image(line.product),
                'quantity': line.quantity,
                'line_price_incl_tax': line.line_price_incl_tax,
                "weight": getattr(
                    line.product.attribute_values.filter(attribute__code='weight').first(), 'value', 'unavailable'
                    ) if not line.product.is_parent else None,
            } for line in consignment.order.lines.all()],
        } for consignment in instance.delivery_consignments.select_related('order', 'order__shipping_address')]

    def get_returns(self, instance):
        def get_return_data(order):
            source = RefundFacade().get_sources_model_from_order(order).first()
            if source:
                return {
                    'payment_type': source.source_type.name,
                    'amount_allocated': source.amount_allocated,
                    'amount_debited': source.amount_debited,
                    'is_paid': source.source_type.code.lower() != 'cash',
                    'amount_refunded': source.amount_refunded,
                    'amount_available_for_refund': source.amount_available_for_refund,
                    'reference': source.reference,
                }
        sel_reltd = 'order_line', 'order_line__order', 'order_line__order__shipping_address'
        items = instance.return_consignments.select_related(*sel_reltd)
        grouped_list = defaultdict(list)

        for item in items:
            source = RefundFacade().get_sources_model_from_order(item.order_line.order).first()
            item.order_line.order.source = None
            if source:
                item.order_line.order.source = {
                    'payment_type': source.source_type.name,
                    'amount_allocated': source.amount_allocated,
                    'amount_debited': source.amount_debited,
                    'is_paid': source.source_type.code.lower() != 'cash',
                    'amount_refunded': source.amount_refunded,
                    'amount_available_for_refund': source.amount_available_for_refund,
                    'reference': source.reference,
                }
            grouped_list[item.order_line.order].append(item)

        return [{
            'order_id': order.id,
            'order_number': order.number,
            'date_placed': order.date_placed,
            'order_status': order.status,
            'num_items_to_be_returned': len(consignments),
            'order_total': currency(order.total_incl_tax),
            'return_amount': '',
            'shipping': {
                'address': order.shipping_address.summary,
                'contact': str(order.shipping_address.phone_number),
                'notes': order.shipping_address.notes,
            },
            'refund': get_return_data(order),
            "consignments": [{
                'id': cons.order_line.id,
                'order_status': cons.order_line.status,
                'consignment_return_id': cons.id,
                'product': {
                    'product_name': cons.order_line.product.name,
                    # 'primary_image': getattr(cons.order_line.product.primary_image(), 'original', None),
                    'quantity': cons.order_line.quantity,
                    'line_price_incl_tax': cons.order_line.line_price_incl_tax
                },
            } for cons in consignments],
        } for order, consignments in grouped_list.items()]

    def get_cod_to_collect(self, instance: DeliveryTrip):
        delivery_consignments_all = instance.delivery_consignments.all()
        return_consignments_all = instance.return_consignments.all()
        approached_statuses = Constant.COMPLETED, Constant.CANCELLED

        delivery_consignments_completed = [cons for cons in delivery_consignments_all if cons.status in approached_statuses]
        return_consignments_completed = [cons for cons in return_consignments_all if cons.status in approached_statuses]
        delivery_consignments_on_going = [cons for cons in delivery_consignments_all if cons.status == Constant.ON_TRIP]
        return_consignments_on_going = [cons for cons in return_consignments_all if cons.status == Constant.ON_TRIP]
        from functools import reduce

        d_to_collect = d_collected = r_to_collect = r_collected = Decimal('0.0')

        return {
            'delivery': instance.cods_to_collect,
            'return': instance.cods_to_return,
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


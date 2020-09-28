from collections import defaultdict
from decimal import Decimal

from oscar.templatetags.currency_filters import currency
from rest_framework import serializers

from apps.api_set.serializers.mixins import ProductPrimaryImageFieldMixin, ProductAttributeFieldMixin
from apps.logistics.models import DeliveryTrip, Constant, NOTE_BY_DELIVERY_BOY
from apps.payment.refunds import RefundFacade


class DeliveryTripSerializer(serializers.ModelSerializer):
    orders = serializers.SerializerMethodField()
    returns = serializers.SerializerMethodField()
    cod_to_collect = serializers.SerializerMethodField()

    @staticmethod
    def get_note(order):
        note = order.notes.filter(note_type=NOTE_BY_DELIVERY_BOY).last()
        if note:
            return note.message

    def get_orders(self, instance):

        def get_source_data(order):
            source = RefundFacade().get_sources_model_from_order(order).first()
            if source:
                return {
                    'payment_type': source.source_type.name,
                    # 'amount_allocated': source.amount_allocated,
                    # 'amount_debited': source.amount_debited,
                    # 'is_paid': source.source_type.code.lower() != 'cash',
                    # 'amount_refunded': source.amount_refunded,
                    # 'amount_available_for_refund': source.amount_available_for_refund,
                    'reference': source.reference,
                }
        return [{
            'consignment_id': consignment.id,
            'id': consignment.order.id,
            'order_number': consignment.order.number,
            'type': 'order',
            'consignment_status': consignment.status,
            'source': get_source_data(consignment.order),
            'order_status': consignment.order.status,
            'date_placed': consignment.order.date_placed,
            'total_incl_tax': consignment.order.total_incl_tax,
            'user_name': consignment.order.shipping_address.get_full_name(),
            'shipping': consignment.order.shipping_address.summary_line,
            'contact': str(consignment.order.shipping_address.phone_number),
            'notes': consignment.order.shipping_address.notes,
            'geolocation': consignment.order.shipping_address.location_data,
            'lines': [{
                'line_id': line.id,
                'line_status': line.status,
                'product_name': line.product.name,
                'quantity': line.quantity,
                'line_price_incl_tax': line.line_price_incl_tax,
                "weight": getattr(
                    line.product.attribute_values.filter(attribute__code='weight').first(), 'value', 'unavailable'
                    ) if not line.product.is_parent else None,
            } for line in consignment.order.lines.all()],
            "cancel_notes": self.get_note(consignment.order),
        } for consignment in instance.delivery_consignments.select_related('order', 'order__shipping_address')]

    def get_returns(self, instance):
        def get_return_data(order):
            source = RefundFacade().get_sources_model_from_order(order).first()
            if source:
                return {
                    'payment_type': source.source_type.name,
                    'reference': source.reference,
                }
        sel_reltd = 'order_line', 'order_line__order', 'order_line__order__shipping_address'
        return_items = instance.return_consignments.select_related(*sel_reltd)

        def get_status(cons):
            is_cancelled = True
            for con in cons:
                if con.status == DeliveryTrip.ON_TRIP:
                    return DeliveryTrip.ON_TRIP
                if con.status != DeliveryTrip.CANCELLED:
                    is_cancelled = False
            return (is_cancelled and DeliveryTrip.CANCELLED) or DeliveryTrip.COMPLETED

        return [{
            'consignment_id': consignment.id,
            'order_id': consignment.order_line.order.id,
            'order_number': consignment.order_line.order.number,
            'id': consignment.order_line.id,
            'type': 'return',
            'consignment_status': consignment.status,
            'source': get_return_data(consignment.order_line.order),
            'order_status': consignment.order_line.status,
            'date_placed': consignment.order_line.order.date_placed,
            'total_incl_tax': consignment.order_line.line_price_incl_tax,
            'user_name': consignment.order_line.order.shipping_address.get_full_name(),
            'shipping': consignment.order_line.order.shipping_address.summary_line,
            'contact': str(consignment.order_line.order.shipping_address.phone_number),
            'notes': consignment.order_line.order.shipping_address.notes,
            'geolocation': consignment.order_line.order.shipping_address.location_data,
            'lines': [{
                'line_id': line.id,
                'line_status': line.status,
                'product_name': line.product.name,
                'quantity': line.quantity,
                'line_price_incl_tax': line.line_price_incl_tax,
                "weight": getattr(
                    line.product.attribute_values.filter(attribute__code='weight').first(), 'value', 'Weight Unavailable'
                ) if not line.product.is_parent else None,
            } for line in [consignment.order_line]],
            "cancel_notes": self.get_note(consignment.order_line.order),
        } for consignment in return_items]

        # return [{
        #     'consignment_id': None,
        #     'id': order.id,
        #     'order_number': order.number,
        #     'type': 'return',
        #     'date_placed': order.date_placed,
        #     'order_status': get_status(consignments),
        #     'order_total': currency(sum(map(lambda con: con.order_line.line_price_incl_tax, consignments))),
        #     'user_name': order.shipping_address.get_full_name(),
        #     'shipping': order.shipping_address.summary_line,
        #     'contact': str(order.shipping_address.phone_number),
        #     'notes': order.shipping_address.notes,
        #     'source': get_re0turn_data(order),
        #     "consignments": [{
        #         'id': cons.order_line.id,
        #         'consignment_return_id': cons.id,
        #         'order_status': cons.order_line.status,
        #         'product': {
        #             'product_name': cons.order_line.product.name,
        #             'primary_image': getattr(cons.order_line.product.primary_image(), 'original', None),
        #             # 'quantity': cons.order_line.quantity,
        #             'line_price_incl_tax': cons.order_line.line_price_incl_tax
        #     #     },
        #   # } for cons in consignments],
        # } for order, consignments in grouped_list.items()]

    def get_cod_to_collect(self, instance: DeliveryTrip):
        return {
            'delivery': instance.cods_to_collect,
            'return': instance.cods_to_return,
        }

    class Meta:
        model = DeliveryTrip
        fields = (
            'id', 'route', 'info', 'updated_at',
            'orders', 'returns', 'cod_to_collect',
        )


class ArchivedTripListSerializer(serializers.ModelSerializer):

    class Meta:
        model = DeliveryTrip
        fields = ('id', 'route', 'info', 'trip_date', 'trip_time', 'cods_to_collect', 'cods_to_return', 'status', )

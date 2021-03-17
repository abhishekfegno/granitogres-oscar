from collections import OrderedDict

from django.conf import settings
from oscar.core.loading import get_model
from oscar.templatetags.currency_filters import currency
from rest_framework import serializers
from rest_framework.relations import HyperlinkedIdentityField

from apps.api_set.serializers.catalogue import ProductListSerializer, ProductSimpleListSerializer, \
    custom_ProductListSerializer
from apps.catalogue.models import Product
from apps.payment.refunds import RefundFacade

Order = get_model('order', 'Order')
Line = get_model('order', 'Line')


class LineDetailSerializer(serializers.ModelSerializer):
    product = ProductListSerializer()

    def get_product(self, instance):
        product_as_qs = Product.objects.filter(id=instance.product_id)
        return custom_ProductListSerializer(product_as_qs, context=self.context).data

    class Meta:
        model = Line
        fields = (
            'id', 'product', 'quantity',
            'line_price_incl_tax',
            'status', 'description', 'product'
        )


class OrderListSerializer(serializers.ModelSerializer):
    url = HyperlinkedIdentityField('api-orders-detail')
    lines = LineDetailSerializer(many=True)
    is_returnable = serializers.SerializerMethodField()
    is_cancellable = serializers.SerializerMethodField()
    can_return_until = serializers.SerializerMethodField()

    def get_is_returnable(self, instance):
        order = instance
        if not order.delivery_time:
            return {
                'status': False,
                'reason': 'Order is not yet delivered!'
            }
        if order.is_return_time_expired:
            return {
                'status': False,
                'reason': 'Return Time Elapsed.'
            }
        if order.lines.filter(status___in=[
            settings.ORDER_STATUS_RETURN_REQUESTED,
            settings.ORDER_STATUS_RETURN_APPROVED,
            settings.ORDER_STATUS_RETURNED
        ]).exists():
            return {
                'status': False,
                'reason': 'You already have initiated / processed a return request.'
            }

        return {
                'status': True,
                'reason': f'You can return any item within ' + str(order.max_time_to__return)
            }

    def get_is_cancellable(self, instance):
        return instance.is_cancelable

    def get_can_return_until(self, instance):
        return instance.max_time_to__return

    class Meta:
        model = Order
        fields = (
            'id', 'number', 'currency', 'total_incl_tax',
            'num_lines', 'status', 'url', 'date_placed', 'lines',
            'is_returnable', 'is_cancellable', 'can_return_until'
        )


class OrderDetailSerializer(serializers.ModelSerializer):
    lines = LineDetailSerializer(many=True)
    total_discount_incl_tax = serializers.SerializerMethodField()
    source = serializers.SerializerMethodField()

    def get_total_discount_incl_tax(self, instance):
        return str(instance.total_discount_incl_tax)

    def get_source(self, order):
        source = RefundFacade().get_sources_model_from_order(order)
        if source:
            return {
                'payment_type': source.source_type.name,
                'amount_debited': source.amount_debited,
                'is_paid': source.source_type.code.lower() != 'cash',
                'amount_refunded': source.amount_refunded,
                'amount_available_for_refund': source.amount_available_for_refund,
                'reference': source.reference,
            }

    class Meta:
        model = Order
        fields = (
            'id', 'number', 'currency',
            'total_discount_incl_tax',
            'shipping_incl_tax',
            'total_incl_tax',
            'shipping_status',
            'source',
            'num_lines', 'status', 'date_placed', 'lines'
        )


class OrderMoreDetailSerializer(serializers.ModelSerializer):
    shipping = serializers.SerializerMethodField()
    # tax_split = serializers.SerializerMethodField()
    payment = serializers.SerializerMethodField()
    discounts = serializers.SerializerMethodField()
    notes = serializers.SerializerMethodField()
    status_changes = serializers.SerializerMethodField()
    shipping_events = serializers.SerializerMethodField()
    payment_events = serializers.SerializerMethodField()

    def get_shipping(self, instance):
        def _inst(attr, default=None):
            if instance.shipping_address:
                return getattr(instance.shipping_address, attr)
            return default
        return {
            'method': instance.shipping_method,
            'address': _inst('summary'),
            'address_type': _inst('address_type'),
            'tax': {
                'excl_tax': currency(instance.shipping_excl_tax, instance.currency),
                'tax': currency(instance.shipping_tax, instance.currency),
                'incl_tax': currency(instance.shipping_incl_tax, instance.currency),
            },
            'contact': str(_inst('phone_number')),
            'notes': _inst('notes'),
        }

    def get_payment(self, instance):
        def _inst(attr, default=None):
            if instance.billing_address:
                return getattr(instance.billing_address, attr)
            return default
        return {
            'billing_address': instance.billing_address.summary if instance.billing_address else None,
            'payment_sources': [{
                'type': str(source.source_type),
                'amount_allocated': currency(source.amount_allocated, instance.currency),
                'amount_debited': currency(source.amount_debited, instance.currency),
                'amount_refunded': currency(source.amount_refunded, instance.currency),
                'reference': source.reference,
            } for source in instance.sources.all()]
        }

    def get_discounts(self, instance):
        return [{
            'category': discount.category,
            'offer_name': discount.offer_name,
            'amount': currency(discount.amount, instance.currency),
            'summary': str(discount),
        } for discount in instance.discounts.all().order_by('id')]

    def get_notes(self, instance):
        return [{
            'note_type': note.note_type,
            'message': note.message,
            'date_updated': note.date_updated,
        } for note in instance.notes.all().order_by('-date_updated')]

    def get_status_changes(self, instance):
        return [{
            'old_status': None,
            'new_status': settings.ORDER_STATUS_PLACED,
            'date_created': instance.date_placed,
        }] + [{
            'old_status': status.old_status,
            'new_status': status.new_status,
            'date_created': status.date_created,
        } for status in instance.status_changes.all().order_by('id')]

    def get_shipping_events(self, instance):
        events = instance.shipping_events.order_by(
            '-date_created', '-pk').select_related('event_type').prefetch_related('line_quantities').all()
        if not len(events):
            return None
        # Collect all events by event-type
        event_map = []
        for event in events:
            event_name = event.event_type.name
            event_map.append({
                'event': event_name,
                'date_created': event.date_created,
                'amount': event.amount,
                'reference': event.amount,
                'lines': "\n ".join([f"{seq.quantity} X {seq.line.product.get_title()}"
                                     for seq in event.line_quantities.all()])
            })
        return event_map

    def get_payment_events(self, instance):
        events = instance.payment_events.order_by(
            '-date_created', '-pk'
        ).select_related('event_type').prefetch_related('line_quantities').all()
        if not len(events):
            return None
        event_map = []
        for event in events:
            event_name = event.event_type.name
            event_map.append({
                'event': event_name,
                'date_created': event.date_created,
                'amount': event.amount,
                'reference': event.amount,
                'lines': "\n ".join([f"{peq.quantity} X {peq.line.product.get_title()}"
                                     for peq in event.line_quantities.all()])
            })
        return event_map

    class Meta:
        model = Order
        fields = (
            'id',
            'num_lines',
            'num_items',
            'shipping', 'payment', 'discounts', 'notes',
            'status_changes', 'shipping_events', 'payment_events'
        )







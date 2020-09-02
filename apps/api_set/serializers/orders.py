from collections import OrderedDict

from oscar.core.loading import get_model
from oscar.templatetags.currency_filters import currency
from rest_framework import serializers
from rest_framework.relations import HyperlinkedIdentityField

from apps.api_set.serializers.catalogue import ProductListSerializer, ProductSimpleListSerializer, \
    custom_ProductListSerializer
from apps.catalogue.models import Product

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

    class Meta:
        model = Order
        fields = (
            'id', 'number', 'currency', 'total_incl_tax',
            'num_lines', 'status', 'url', 'date_placed', 'lines'
        )


class OrderDetailSerializer(serializers.ModelSerializer):
    lines = LineDetailSerializer(many=True)
    total_discount_incl_tax = serializers.SerializerMethodField()

    def get_total_discount_incl_tax(self, instance):
        return str(instance.total_discount_incl_tax)

    class Meta:
        model = Order
        fields = (
            'id', 'number', 'currency',
            'total_discount_incl_tax',
            'shipping_incl_tax',
            'total_incl_tax',
            'shipping_status',
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







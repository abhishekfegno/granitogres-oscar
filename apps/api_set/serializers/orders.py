from collections import OrderedDict

from django.conf import settings
from oscar.core.loading import get_model
from oscar.templatetags.currency_filters import currency
from oscarapi.serializers.checkout import ShippingAddressSerializer, BillingAddressSerializer, \
    InlineShippingAddressSerializer, InlineBillingAddressSerializer
from rest_framework import serializers
from rest_framework.relations import HyperlinkedIdentityField

from apps.api_set.serializers.catalogue import ProductListSerializer
from apps.api_set_v2.serializers.catalogue import ProductSimpleListSerializer, custom_ProductListSerializer
from apps.order.models import Order, Line
from apps.payment.refunds import RefundFacade
from apps.payment.utils.cash_payment import Cash
from apps.utils.utils import get_statuses
from osc.config.oscar import OSCAR_ORDER_STATUS_PIPELINE


class ProductListSerializerForLine(ProductListSerializer):

    def get_primary_image(self, instance, ignore_if_child=False):
        return super(ProductListSerializer, self).get_primary_image(instance, ignore_if_child=ignore_if_child)


class LineDetailSerializer(serializers.ModelSerializer):
    product = ProductListSerializerForLine()
    # product = serializers.SerializerMethodField()
    has_reviewed = serializers.SerializerMethodField()

    def get_has_reviewed(self, instance):
        from apps.catalogue.reviews.models import ProductReview
        if instance.order.status in (
            settings.ORDER_STATUS_DELIVERED
        ):
            return ProductReview.objects.filter(product_id=instance.product_id, user=self.context['request'].user).exists()
        # returning True as default!
        # this doesn't mean user has reviewed, but helps not to review on non delivered or return triggered orders.
        return True

    def get_product(self, instance):
        return custom_ProductListSerializer([instance.product], context=self.context, ignore_child_image=False).data

    class Meta:
        model = Line
        fields = (
            'id', 'product', 'quantity',
            'line_price_incl_tax', 'has_reviewed',
            'status', 'description', 'product', 'title'
        )


class OrderListSerializer(serializers.ModelSerializer):
    url = HyperlinkedIdentityField('api-orders-detail')
    lines = LineDetailSerializer(many=True)
    is_returnable = serializers.SerializerMethodField()
    is_cancellable = serializers.SerializerMethodField()
    can_return_until = serializers.SerializerMethodField()

    def get_is_returnable(self, instance):
        order = instance
        if not order.delivery_time or order.status != settings.ORDER_STATUS_DELIVERED:
            return {
                'status': False,
                'reason': 'Order is not yet delivered!'
            }
        if order.is_return_time_expired:
            return {
                'status': False,
                'reason': 'Return Time Elapsed.'
            }
        if order.lines.filter(status__in=[
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
        return str(instance.max_time_to__return)

    class Meta:
        model = Order
        fields = (
            'id', 'number', 'currency',
            'total_incl_tax',
            'num_lines', 'status', 'url', 'date_placed', 'lines',
            'is_returnable', 'is_cancellable', 'can_return_until'
        )


class OrderDetailSerializer(serializers.ModelSerializer):
    lines = LineDetailSerializer(many=True)
    total_discount_incl_tax = serializers.SerializerMethodField()
    source = serializers.SerializerMethodField()
    info = serializers.SerializerMethodField()
    should_show_line_status = serializers.SerializerMethodField()
    billing_address = serializers.SerializerMethodField()
    shipping_address = serializers.SerializerMethodField()

    def get_shipping_address(self, instance):
        return InlineShippingAddressSerializer(instance.shipping_address, context=self.context).data

    def get_billing_address(self, instance):
        return InlineBillingAddressSerializer(instance.billing_address, context=self.context).data

    def get_return_lines(self, instance):
        return instance.lines.filter(status__in=get_statuses(112))

    def get_info(self, instance) -> dict:
        is_cancelled = instance.status == settings.ORDER_STATUS_CANCELED
        has_cancelled_items = any([
            line.status == settings.ORDER_STATUS_CANCELED
            for line in instance.lines.all()
        ])
        SUCCESS = 'success'
        WARNING = 'warning'
        HIDDEN = 'hide'
        DANGER = 'error'

        if instance.status == settings.ORDER_STATUS_PLACED:
            return {
                'type': SUCCESS,
                'has_cancelled_items': has_cancelled_items,
                'message': "Your Order has been placed!",
            }
        if instance.status == settings.ORDER_STATUS_CONFIRMED:
            return {
                'type': SUCCESS,
                'has_cancelled_items': has_cancelled_items,
                'message': "We are preparing your basket!"
            }
        if is_cancelled:
            return {
                'type': HIDDEN,
                'has_cancelled_items': has_cancelled_items,
                'message': ""
            }
        elif has_cancelled_items and instance.status == settings.ORDER_STATUS_CONFIRMED:
            return {
                'type': WARNING,
                'has_cancelled_items': has_cancelled_items,
                'message': ""
            }

        if instance.status == settings.ORDER_STATUS_OUT_FOR_DELIVERY:
            return {
                'type': WARNING,
                'has_cancelled_items': has_cancelled_items,
                'message': "We are about to reach you!"
            }
        if instance.status == settings.ORDER_STATUS_DELIVERED:
            return {
                'type': HIDDEN,
                'has_cancelled_items': has_cancelled_items,
                'message': ""
            }

        if instance.status == settings.ORDER_STATUS_RETURN_REQUESTED:
            return {
                'type': WARNING,
                'has_cancelled_items': has_cancelled_items,
                'message': "You Will receive a call from us!"
            }
        if instance.status == settings.ORDER_STATUS_RETURN_APPROVED:
            return {
                'type': WARNING,
                'has_cancelled_items': has_cancelled_items,
                'message': "The return will be picked up soon!"
            }

        if instance.status == settings.ORDER_STATUS_RETURNED:
            return {
                'type': WARNING,
                'has_cancelled_items': has_cancelled_items,
                'message': "The return will be picked up soon!"
            }

        return_statuses = [s.status for s in self.get_return_lines(instance)]
        if settings.ORDER_STATUS_RETURNED in return_statuses:
            return {
                'type': WARNING,
                'has_cancelled_items': has_cancelled_items,
                'message': "Partially returned"
            }
        elif settings.ORDER_STATUS_RETURN_APPROVED in return_statuses:
            return {
                'type': WARNING,
                'has_cancelled_items': has_cancelled_items,
                'message': "Returned approved!"
            }
        elif settings.ORDER_STATUS_RETURN_REQUESTED in return_statuses:
            return {
                'type': WARNING,
                'has_cancelled_items': has_cancelled_items,
                'message': "Return request waiting for approval"
            }
        return {
            'type': SUCCESS,
            'has_cancelled_items': has_cancelled_items,
            'message': ""
        }

    def get_should_show_line_status(self, instance) -> bool:
        return instance.status in get_statuses(240)

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

    total_excl_tax = serializers.SerializerMethodField()

    def get_total_excl_tax(self, instance):
        return float(instance.total_excl_tax)

    shipping_incl_tax = serializers.SerializerMethodField()

    def get_shipping_incl_tax(self, instance):
        return float(instance.shipping_incl_tax)

    total_tax = serializers.SerializerMethodField()

    def get_total_tax(self, instance):
        return float(instance.total_tax)

    total_incl_tax = serializers.SerializerMethodField()

    def get_total_incl_tax(self, instance):
        return float(instance.total_incl_tax)

    is_returnable = serializers.SerializerMethodField()
    is_cancellable = serializers.SerializerMethodField()
    can_return_until = serializers.SerializerMethodField()
    max_time_to__return = serializers.SerializerMethodField()

    def get_is_returnable(self, instance):
        order = instance
        if not order.delivery_time or order.status != settings.ORDER_STATUS_DELIVERED:
            return {
                'status': False,
                'reason': 'Order is not yet delivered!'
            }
        if order.is_return_time_expired:
            return {
                'status': False,
                'reason': 'Return Time Elapsed.'
            }
        if order.lines.filter(status__in=[
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

    def get_max_time_to__return(self, instance):
        return str(instance.max_time_to__return)

    def get_can_return_until(self, instance):
        return str(instance.max_time_to__return)

    class Meta:
        model = Order
        fields = (
            'id', 'number', 'currency',
            'basket_total_before_discounts_excl_tax',
            'basket_total_before_discounts_incl_tax',
            'total_discount_incl_tax',
            'shipping_incl_tax',
            'total_tax',
            'total_excl_tax',
            'total_incl_tax',
            'shipping_status',
            'source',
            "shipping_address",
            "billing_address",
            'should_show_line_status',
            'max_time_to__return',
            'num_lines', 'status', 'date_placed', 'lines', 'info',
            'is_returnable', 'is_cancellable', 'can_return_until',

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
            } for source in instance.sources.all().select_related('source_type')]
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
        out = []

        init = {
            status.new_status: {
                'old_status': status.old_status,
                'new_status': status.new_status,
                'date_created': status.date_created,        # issue 2. date not comming
            } for status in instance.status_changes.all().order_by('id')
        }

        added_statuses = list(init.keys())
        is_cancelled = settings.ORDER_STATUS_CANCELED in added_statuses
        is_return_initiated = settings.ORDER_STATUS_RETURN_REQUESTED in added_statuses

        if not is_return_initiated:
            """
            From Placed to Delivered or Placed to Cancelled
            """
            items = sorted(settings.OSCAR_ORDER_STATUS_UNTIL_DELIVER, key=lambda x: x[0])

            if not is_cancelled:
                """
                From Placed to Delivered.
                """
                earlier_status = None
                for display_order, status in items:
                    if status in init:
                        out.append(init[status])
                    else:
                        out.append({
                            'old_status': earlier_status,
                            'new_status': status,
                            'date_created': None
                        })
                    earlier_status = status
            else:
                """
                Placed to Cancelled.
                
                """
                # status_to_cancel = OSCAR_ORDER_STATUS_PIPELINE
                # for status_ in status_to_cancel:
                #
                #     if status_ == instance.status:
                #         out.append({
                #             'old_status': instance.status,
                #             'new_status': OSCAR_ORDER_STATUS_PIPELINE[instance.status][-1],
                #             'date_created': instance.date_placed
                #         })


                is_cod = instance.sources.all().select_related('source_type').last().source_type.name == Cash.name
                if settings.ORDER_STATUS_PLACED not in init:
                    """
                    To add "Placed" for order status which do not have a "Placed" status in "status_changes".
                    """
                    """ all status to canceled """

                    out.append({
                        'old_status': None,
                        'new_status': settings.ORDER_STATUS_PLACED,
                        'date_created': instance.date_placed,  # issue 2. date not comming
                    })
                statuses = OSCAR_ORDER_STATUS_PIPELINE

                out += list(init.values())
                if not is_cod:
                    """ if Online Payment. """
                    out.append({
                        'old_status': out[-1]['new_status'],
                        'new_status': 'Refund Initiated',
                        'date_created': out[-1]['date_created']
                    })
        else:
            """
            From Delivered to Returned
            """

            earlier_status = None
            for returned_status in settings.OSCAR_ADMIN_LINE_POST_DELIVERY_ORDER_STATUSES:
                if returned_status in init:
                    out.append(init[returned_status])
                else:
                    out.append({
                        'old_status': None,
                        'new_status': returned_status,
                        'date_created': None
                    })
                earlier_status = returned_status
            if settings.ORDER_STATUS_RETURNED in init:
                out.append({
                    'old_status': out[-1]['new_status'],
                    'new_status': 'Return Initiated',
                    'date_created': out[-1]['date_created']
                })
        if len(out):
            out[0]['date_created'] = instance.date_placed

        return out

    def get_shipping_events(self, instance):
        return None
        # events = instance.shipping_events.order_by(
        #     '-date_created', '-pk').select_related('event_type').prefetch_related('line_quantities').all()
        # if not len(events):
        #     return None
        # # Collect all events by event-type
        # event_map = []
        # for event in events:
        #     event_name = event.event_type.name
        #     event_map.append({
        #         'event': event_name,
        #         'date_created': event.date_created,
        #         'lines': "\n ".join([f"{seq.quantity} X {seq.line.title}"
        #                              for seq in event.line_quantities.all()])
        #     })
        # return event_map

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
                'lines': "\n ".join([f"{peq.quantity} X {peq.line.title}"
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







import datetime
from collections import defaultdict
from django.utils import timezone
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Q, Sum
from django.utils.functional import cached_property
from oscar.apps.payment.models import Source
from oscar.core.loading import get_model
from oscar.core.utils import get_default_currency
from oscar.templatetags.currency_filters import currency

from . import settings as app_settings
from ..order.processing import EventHandler
from ..payment.refunds import RefundFacade
from ..payment.utils.cash_payment import Cash

Order = get_model('order', 'Order')
OrderLine = get_model('order', 'Line')

NOTE_BY_DELIVERY_BOY = "Reason From Delivery App"


class Constant:
    ON_TRIP = 'On Trip'
    COMPLETED = 'Completed'
    CANCELLED = 'Cancelled'
    YET_TO_START = 'Yet to Start'
    CHOICES = [
        (ON_TRIP, ON_TRIP),
        (CANCELLED, CANCELLED),
        (COMPLETED, COMPLETED),
        (YET_TO_START, YET_TO_START),
    ]

    @property
    def is_under_planning(self):
        return self.status == self.YET_TO_START

    @property
    def on_trip(self):
        return self.status == self.ON_TRIP

    @property
    def is_completed(self):
        return self.status == self.COMPLETED

    @property
    def is_cancelled(self):
        return self.status == self.CANCELLED

    @property
    def css_badge_class(self):
        if self.is_under_planning:
            return 'badge badge-info'
        elif self.on_trip:
            return 'badge badge-primary'
        elif self.is_completed:
            return 'badge badge-success'
        elif self.is_cancelled:
            return 'badge badge-danger'
        return 'badge'

    @cached_property
    def transaction_source_n_method(self):
        raise NotImplementedError('transaction_source_n_method')

    @property
    def transaction_source(self):
        raise self.transaction_source_n_method[0]

    @cached_property
    def transaction_type(self):
        return self.transaction_source.source_type.name

    @cached_property
    def transaction_amount(self):
        return {
            'allocated': self.transaction_source.amount_allocated,
            'debited': self.transaction_source.amount_debited,
            'refunded': self.transaction_source.amount_refunded,
        }


class DeliveryTrip(Constant, models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    agent = models.ForeignKey(app_settings.AGENT_MODEL, on_delete=models.CASCADE)
    status = models.CharField(choices=Constant.CHOICES, default=Constant.YET_TO_START, max_length=20)
    trip_date = models.DateField(null=True, blank=True, db_index=True)
    trip_time = models.TimeField(null=True, blank=True)
    route = models.CharField(max_length=128, null=True, blank=True)
    info = models.CharField(max_length=256, null=True, blank=True)
    reason = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.agent} on {self.created_at} {self.status}"

    @property
    def is_editable(self):
        return self.is_under_planning

    def have_active_consignments(self):
        return (
                self.delivery_consignments.exclude(status__in=[self.COMPLETED, self.CANCELLED]).exists()
                or
                self.return_consignments.exclude(status__in=[self.COMPLETED, self.CANCELLED]).exists()
        )

    @property
    def have_consignments(self):
        return self.delivery_consignments.exists() or self.return_consignments.exists()

    @property
    def delivery_orders(self):
        return Order.objects.filter(consignmentdelivery__delivery_trip=self)

    @property
    def delivery_returns(self):
        return OrderLine.objects.filter(consignmentreturn__delivery_trip=self)

    @property
    def possible_delivery_orders(self):
        qs = ConsignmentDelivery.objects.filter(delivery_trip__isnull=True)
        if self.pk:
            qs |= ConsignmentDelivery.objects.filter(delivery_trip=self)
        return qs.select_related('delivery_trip', 'order', 'order__shipping_address', 'order__user', )

    @property
    def possible_delivery_returns(self):
        qs = ConsignmentReturn.objects.filter(delivery_trip__isnull=True)
        if self.pk:
            qs |= ConsignmentReturn.objects.filter(delivery_trip=self)
        return qs.select_related('delivery_trip', 'order_line',
                                 'order_line__order',
                                 'order_line__order__user',
                                 'order_line__order__shipping_address')

    def update_self(self):
        self.trip_date = datetime.date.today()
        self.trip_time = timezone.now().time()
        self.status = self.COMPLETED
        self.save()

    def mark_as_completed(self):
        """
        In the assumption that, 'request_cancelled' can be set by user.
        """
        assert not self.delivery_consignments.exclude(status__in=[self.COMPLETED, self.CANCELLED]).exists(), \
            "Could mark as complete because there are incomplete delivery consignments."

        assert not self.return_consignments.exclude(status__in=[self.COMPLETED, self.CANCELLED]).exists(), \
            "Could mark as complete because there are incomplete delivery consignments."

        """ Handling Pickup. """
        self.update_self()

    def complete_forcefully(self, reason=None):
        # Complete as trip successfully ended!
        """
        In the assumption that, 'request_cancelled' can be set by user.
        ONLY FOR DEBUGGING PURPOSE.
        """
        """ Handling Delivery. """
        for consignment in self.delivery_consignments.exclude(status=Constant.COMPLETED).all():
            consignment.mark_as_completed()

        """ Handling Pickup and Pickup Cancellation. """
        for consignment in self.return_consignments.exclude(status=Constant.COMPLETED, request_cancelled=True):
            consignment.mark_as_completed()

        """ Handling Pickup. """
        self.update_self()

    @classmethod
    def get_active_trip(cls, agent, raise_error=True):
        try:
            return cls.objects.get(agent=agent, status=cls.ON_TRIP)
        except Exception as e:
            if raise_error:
                raise e
            if type(e) is cls.MultipleObjectsReturned:
                return cls.objects.filter(agent=agent, status=cls.ON_TRIP).last()

    def agent_do_not_have_other_active_trips(self):
        return not self.__class__.objects.filter(agent=self.agent, status=self.ON_TRIP).exists()

    def activate_trip(self):
        """
        Changes status of all Orders to "Out for Delivery" Mode.
        """
        # there should not be any other active trips for this user.
        assert self.have_consignments
        assert self.agent_do_not_have_other_active_trips()
        self.status = self.ON_TRIP
        self.trip_date = datetime.date.today()
        self.trip_time = timezone.now().time()
        order_status = app_settings.LOGISTICS_ORDER_STATUS_ON_TRIP_ACTIVATE
        for order in self.delivery_orders:
            if order_status in order.available_statuses():
                order.set_status(order_status)
        self.delivery_consignments.update(status=Constant.ON_TRIP)
        self.return_consignments.update(status=Constant.ON_TRIP)
        self.save()

    def get_completed(self):
        if self.status == self.COMPLETED:
            return True
        if not self.have_active_consignments():
            self.status = self.COMPLETED
            self.save()
        return self.status == self.COMPLETED

    def cancel_consignment(self, reason=''):
        for dc in self.delivery_consignments.all():
            dc.cancel_consignment(reason)
        for dc in self.return_consignments.all():
            dc.cancel_consignment(reason)
        self.status = self.CANCELLED
        self.save()

    @cached_property
    def cods_to_collect(self):
        sources = Source.objects.filter(
            order__in=self.delivery_orders.all()
        ).select_related('order', 'source_type')
        net = Decimal('0.0')
        for source in sources:
            if source.source_type.name == Cash.name:
                net += source.order.total_incl_tax
        return currency(net, get_default_currency())

    @cached_property
    def cods_to_return(self):
        order_set = defaultdict(list)
        for item in self.delivery_returns.all():
            order_set[item.order].append(item)

        sources = Source.objects.filter(
            order__in=order_set.keys()
        ).select_related('order', 'source_type')
        net = Decimal('0.0')
        for source in sources:
            if source.source_type.name == Cash.name:
                for item in order_set[source.order]:
                    net += item.line_price_incl_tax
        return currency(net, get_default_currency())


class ConsignmentDelivery(Constant, models.Model):
    order: Order = models.OneToOneField('order.Order', on_delete=models.CASCADE)
    delivery_trip: DeliveryTrip = models.ForeignKey('logistics.DeliveryTrip', on_delete=models.CASCADE, null=True, blank=True,
                                                    related_name='delivery_consignments')
    status = models.CharField(choices=Constant.CHOICES, default=Constant.YET_TO_START, max_length=20)
    reason = models.TextField(null=True, blank=True)

    def mark_as_completed(self, reason=None):
        if hasattr(self, 'order'):
            EventHandler().handle_order_status_change(self.order, settings.ORDER_STATUS_DELIVERED,
                                                      note_msg=reason, note_type=NOTE_BY_DELIVERY_BOY)
        self.status = self.COMPLETED
        self.save()

    def cancel_consignment(self, reason=None):
        if reason is None:
            reason = "Order Could not be delivered, We could not reach you at that point."
        if hasattr(self, 'order'):
            EventHandler().handle_order_status_change(self.order, settings.ORDER_STATUS_CANCELED, note_msg=reason,
                                                      note_type=NOTE_BY_DELIVERY_BOY)
        self.status = self.CANCELLED
        self.save()

    @cached_property
    def transaction_source_n_method(self):
        return RefundFacade().get_source_n_method(self.order)


class ConsignmentReturn(Constant, models.Model):
    order_line = models.ForeignKey('order.Line', on_delete=models.CASCADE)
    delivery_trip = models.ForeignKey('logistics.DeliveryTrip', on_delete=models.CASCADE, null=True, blank=True,
                                      related_name='return_consignments')
    status = models.CharField(choices=Constant.CHOICES, default=Constant.YET_TO_START, max_length=20)
    request_cancelled = models.BooleanField(default=False)
    completed = models.BooleanField(default=False)
    reason = models.TextField(null=True, blank=True)

    @cached_property
    def transaction_source_n_method(self):
        return RefundFacade().get_source_n_method(self.order_line.order)

    @classmethod
    def get_instance_from_line(cls, line, as_queryset=False):
        qs = cls.objects.filter(
            request_cancelled=True, order_line=line, status=cls.COMPLETED)
        if as_queryset:
            return qs
        return qs.last()

    def mark_as_completed(self, reason=None):
        EventHandler().handle_order_line_status_change(self.order_line, settings.ORDER_STATUS_RETURNED,
                                                       note_msg=reason, note_type=NOTE_BY_DELIVERY_BOY)
        self.status = self.COMPLETED
        self.save()

    def cancel_consignment(self, reason=None):
        if reason is None:
            reason = "Item Return could not be delivered."
        EventHandler().handle_order_line_status_change(self.order_line, settings.ORDER_STATUS_DELIVERED,
                                                       note_msg=reason, note_type=NOTE_BY_DELIVERY_BOY)
        self.status = self.CANCELLED
        self.save()

    @classmethod
    def generate(cls, line):
        """
        States :
            1. New Order Return Request.
            2. Re-Return Cancelled Request, which is not cancelled.
            3. Re-Return Cancelled Request, which is already cancelled. (handled as case 1)
        """
        old_pending_return_consignment = cls.get_instance_from_line(line)
        if old_pending_return_consignment:
            """ Handling Case 2 """
            old_pending_return_consignment.request_cancelled = False
            old_pending_return_consignment.save()
            return old_pending_return_consignment
        else:
            """ Handling Case 1 & 3 """
            consignment_return, is_new = cls.objects.exclude(
                status=cls.COMPLETED, request_cancelled=True
            ).get_or_create(order_line=line)
            return consignment_return








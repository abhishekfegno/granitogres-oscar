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
from ..payment.utils.cash_payment import Cash

Order = get_model('order', 'Order')
OrderLine = get_model('order', 'Line')


class DeliveryTrip(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    agent = models.ForeignKey(app_settings.AGENT_MODEL, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=False)   # active mode or in draft mode.
    completed = models.BooleanField(default=False)
    route = models.CharField(max_length=128, null=True, blank=True)
    info = models.CharField(max_length=256, null=True, blank=True)

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
    def is_editable(self):
        return not self.is_active or not self.completed

    @property
    def possible_delivery_returns(self):
        qs = ConsignmentReturn.objects.filter(delivery_trip__isnull=True)
        if self.pk:
            qs |= ConsignmentReturn.objects.filter(delivery_trip=self)
        return qs.select_related('delivery_trip', 'order_line',
                                 'order_line__order',
                                 'order_line__order__user',
                                 'order_line__order__shipping_address')

    def complete_forcefully(self):
        """
        In the assumption that, 'request_cancelled' can be set by user.
        """

        # """ Handling Delivery. """
        # self.delivery_consignments.update(completed=True)
        #
        # """ Updating Status of order for Pickup and Pickup Cancellation. """
        # for consignment in self.return_consignments.all():
        #     if consignment.order_item.request_cancelled is False:
        #         """ Signal will handle refunding procedure and all."""
        #         consignment.order_item.set_state(settings.ORDER_STATUS_RETURNED)
        #     else:
        #         """ Status back to delivered."""
        #         consignment.order_item.set_state(settings.ORDER_STATUS_DELIVERED)
        assert not self.delivery_consignments.filter(completed=False).exists()
        assert not self.return_consignments.filter(completed=False).exists()
        """ Handling Pickup. """
        self.completed = True
        self.save()

    @classmethod
    def active_trip(cls, agent, raise_error=True):
        try:
            return cls.objects.get(agent=agent, is_active=True, completed=False)
        except Exception as e:
            if raise_error:
                raise e
            if type(e) is cls.MultipleObjectsReturned:
                return cls.objects.filter(agent=agent, is_active=True, completed=False).last()

    def activate_trip(self):
        """
        Changes status of all Orders to "Out for Delivery" Mode.
        """
        # there should not be any other active trips for this user.
        assert not self.__class__.active_trip(self.agent, raise_error=False)
        self.is_active = True
        status = app_settings.LOGISTICS_ORDER_STATUS_ON_TRIP_ACTIVATE
        for order in self.delivery_orders():
            if status in order.available_statuses():
                order.set_status(status)
        self.save()

    def get_completed(self):
        if self.completed:
            return True
        self.completed = not any([
            self.delivery_consignments.filter(completed=False).exists(),
            self.return_consignments.filter(Q(completed=False)|Q(request_cancelled=True)).exists(),
        ])
        if self.completed:
            self.save()
        return self.completed

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
        #  TODO : implement
        return Decimal('0.0')


class ConsignmentDelivery(models.Model):
    order = models.OneToOneField('order.Order', on_delete=models.CASCADE)
    delivery_trip = models.ForeignKey('logistics.DeliveryTrip', on_delete=models.CASCADE, null=True, blank=True,
                                      related_name='delivery_consignments')
    completed = models.BooleanField(default=False)

    def mark_as_completed(self):
        self.completed = True
        self.save()


class ConsignmentReturn(models.Model):
    order_line = models.ForeignKey('order.Line', on_delete=models.CASCADE)
    delivery_trip = models.ForeignKey('logistics.DeliveryTrip', on_delete=models.CASCADE, null=True, blank=True,
                                      related_name='return_consignments')
    request_cancelled = models.BooleanField(default=False)
    completed = models.BooleanField(default=False)

    @classmethod
    def get_instance_from_line(cls, line, as_queryset=False):
        qs = cls.objects.filter(
            request_cancelled=True, order_line=line, completed=False)
        if as_queryset:
            return qs
        return qs.last()

    @classmethod
    def cancel_consignment(cls, line):
        cls.get_instance_from_line(line, as_queryset=True).update(request_cancelled=False)

    @classmethod
    def mark_as_completed(cls, line):
        cls.get_instance_from_line(line, as_queryset=True).update(completed=True)

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
            consignment_return, is_new = cls.objects.filter(
                completed=False, request_cancelled=False).get_or_create(order_line=line)
            return consignment_return







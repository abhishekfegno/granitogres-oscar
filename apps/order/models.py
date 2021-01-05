from django.contrib.gis.db.models import PointField
from oscar.apps.address.abstract_models import (
    AbstractBillingAddress, AbstractShippingAddress)
from oscar.apps.order.abstract_models import *

__all__ = ['PaymentEventQuantity', 'ShippingEventQuantity']

from oscar.templatetags.datetime_filters import timedelta

from apps.users.models import Location


class Order(AbstractOrder):

    def is_cancelable(self):
        return bool(self.status in settings.OSCAR_USER_CANCELLABLE_ORDER_STATUS)

    @property
    def last_date_to__return(self):
        delta = timedelta(days=settings.DEFAULT_PERIOD_OF_RETURN)
        return self.date_placed + delta

    @property
    def is_return_date_expired(self):
        return bool(self.last_date_to__return >= timezone.now())


class OrderNote(AbstractOrderNote):
    pass


class OrderStatusChange(AbstractOrderStatusChange):
    pass


class CommunicationEvent(AbstractCommunicationEvent):
    pass


class ShippingAddress(AbstractShippingAddress):
    location = PointField(null=True, blank=True)

    @property
    def summary_line(self):
        """
        Returns a single string summary of the address,
        separating fields using commas.
        """
        fields = ['line1', 'line2', 'line3', 'line4', 'state', 'postcode', 'country']
        return ", ".join(self.get_field_values(fields))

    def get_full_name(self):

        fields = ['salutation', 'first_name', 'last_name']
        return ", ".join(self.get_field_values(fields))

    @property
    def location_data(self):
        return {
            'latitude': self.location and self.location.x,
            'longitude': self.location and self.location.y,
        }


class BillingAddress(AbstractBillingAddress):
    pass


class Line(AbstractLine):
    refunded_quantity = models.PositiveSmallIntegerField(default=0)

    @property
    def last_date_to__return(self):
        delta = timedelta(days=settings.DEFAULT_PERIOD_OF_RETURN)
        return self.order.date_placed + delta

    @property
    def is_return_date_expired(self):
        return bool(self.last_date_to__return >= timezone.now())

    @property
    def active_quantity(self):
        return self.quantity - self.refunded_quantity

    @property
    def is_returnable(self):
        if self.order.is_return_date_expired:
            return False
        if not (self.is_refundable or self.is_replaceable):
            return False
        if self.refunded_quantity:  # is greater than 0
            return False
        return True

    @property
    def is_refundable(self):
        return True

    @property
    def is_replaceable(self):
        return True

    @property
    def could_not_return_message(self):
        if self.status != settings.ORDER_STATUS_DELIVERED:
            return "Return Could not be Initiated as order status is not Delivered."
        elif self.order.is_return_date_expired:
            return "Return Could not be Initiated Last date to Initiate Return is over."
        elif not self.is_replaceable and not self.is_refundable:
            return "Could not Refund or Replace the item."
        elif self.refunded_quantity > 0:
            return "Item already returned or replaced once."
        return None


class LinePrice(AbstractLinePrice):
    pass


class LineAttribute(AbstractLineAttribute):
    pass


class ShippingEvent(AbstractShippingEvent):
    pass


class ShippingEventType(AbstractShippingEventType):
    pass


class PaymentEvent(AbstractPaymentEvent):
    pass


class PaymentEventType(AbstractPaymentEventType):
    pass


class OrderDiscount(AbstractOrderDiscount):
    pass



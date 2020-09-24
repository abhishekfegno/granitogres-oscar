from oscar.apps.address.abstract_models import (
    AbstractBillingAddress, AbstractShippingAddress)
from oscar.apps.order.abstract_models import *

__all__ = ['PaymentEventQuantity', 'ShippingEventQuantity']

from apps.users.models import Location


class Order(AbstractOrder):
    pass


class OrderNote(AbstractOrderNote):
    pass


class OrderStatusChange(AbstractOrderStatusChange):
    pass


class CommunicationEvent(AbstractCommunicationEvent):
    pass


class ShippingAddress(AbstractShippingAddress):
    location = models.ForeignKey('users.Location', on_delete=models.SET_NULL, null=True, blank=True)

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


class BillingAddress(AbstractBillingAddress):
    pass


class Line(AbstractLine):
    refunded_quantity = models.PositiveSmallIntegerField(default=0)

    @property
    def active_quantity(self):
        return self.quantity - self.refunded_quantity


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



from oscar.apps.address.abstract_models import (
    AbstractBillingAddress, AbstractShippingAddress)
from oscar.apps.order.abstract_models import *

__all__ = ['PaymentEventQuantity', 'ShippingEventQuantity']


class Order(AbstractOrder):
    pass


class OrderNote(AbstractOrderNote):
    pass


class OrderStatusChange(AbstractOrderStatusChange):
    pass


class CommunicationEvent(AbstractCommunicationEvent):
    pass


class ShippingAddress(AbstractShippingAddress):
    pass


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



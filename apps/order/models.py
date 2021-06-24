import datetime

from django.contrib.gis.db.models import PointField
from django.core.cache import cache
from django.db.models.signals import post_save
from django.utils.functional import cached_property
from oscar.apps.address.abstract_models import (
    AbstractBillingAddress, AbstractShippingAddress)
from oscar.apps.order.abstract_models import *

__all__ = ['PaymentEventQuantity', 'ShippingEventQuantity', 'Order']

from oscar.models.fields import UppercaseCharField

from apps.users.models import Location
from apps.utils.utils import get_statuses


class Order(AbstractOrder):
    date_delivered = models.DateTimeField(null=True, blank=True, help_text="Date of Consignment Delivery")

    @property
    def preferred_slot_text(self):
        return '10:00AM - 1:00PM'

    @property
    def is_cancelable(self):
        return bool(self.status in settings.OSCAR_USER_CANCELLABLE_ORDER_STATUS)

    @property
    def max_time_to__return(self):
        delta = datetime.timedelta(**settings.DEFAULT_PERIOD_OF_RETURN)
        return self.delivery_time and (self.delivery_time + delta)

    @property
    def is_return_time_expired(self):
        return not self.delivery_time or (self.max_time_to__return and bool(self.max_time_to__return < timezone.now()))

    @cached_property
    def delivery_time(self):
        if self.status in get_statuses(775):
            return None     # as the package is not delivered
        if not self.date_delivered:
            date_delivered = self.status_changes.filter(new_status=settings.ORDER_STATUS_DELIVERED).order_by('date_created').first()
            self.date_delivered = date_delivered and date_delivered.date_created
            self.date_delivered and self.save()
        return self.date_delivered

    cancelled_order_statuses = settings.OSCAR_ORDER_REFUNDABLE_STATUS

    @property
    def cancelled_order_lines(self):
        lines = []
        for line in self.lines.all():
            if line.status in self.cancelled_order_statuses:
                lines.append(line)
        return lines

    @property
    def cancelled_order_amount_excl_tax(self):
        amount = 0
        for line in self.cancelled_order_lines:
            amount += line.line_price_excl_tax
        return amount


    @property
    def cancelled_order_amount_incl_tax(self):
        amount = 0
        for line in self.cancelled_order_lines:
            amount += line.line_price_incl_tax
        return amount

    @property
    def balance_order_amount_after_cancelled_excl_tax(self):
        return self.total_incl_tax - self.cancelled_order_amount_excl_tax

    @property
    def balance_order_amount_after_cancelled_incl_tax(self):
        return self.total_incl_tax - self.cancelled_order_amount_incl_tax


class OrderNote(AbstractOrderNote):
    pass


class OrderStatusChange(AbstractOrderStatusChange):
    pass


class CommunicationEvent(AbstractCommunicationEvent):
    pass


class ShippingAddress(AbstractShippingAddress):
    location = PointField(null=True, blank=True)
    address_type = models.CharField(max_length=12, null=True, blank=True)
    line1 = models.CharField("House No", max_length=255)
    line2 = models.CharField("Apartment Name", max_length=255, blank=True)
    line3 = models.CharField("Street Details", max_length=255, blank=True)
    line4 = models.CharField("Landmark", max_length=255, blank=True)
    line5 = models.CharField("City", max_length=255, blank=True)
    state = models.CharField("State/County", max_length=255, blank=True)
    postcode = UppercaseCharField("Post/Zip-code", max_length=64, blank=True)

    @property
    def house_no(self):
        return self.line1

    @property
    def apartment(self):
        return self.line2

    @property
    def street(self):
        return self.line3

    @property
    def landmark(self):
        return self.line4

    @property
    def city(self):
        return self.line5

    @apartment.setter
    def apartment(self, value):
        self.line2 = value

    @street.setter
    def street(self, value):
        self.line3 = value

    @landmark.setter
    def landmark(self, value):
        self.line4 = value

    @city.setter
    def city(self, value):
        self.line5 = value

    @property
    def summary_line(self):
        """
        Returns a single string summary of the address,
        separating fields using commas.
        """
        fields = ['line1', 'line2', 'line3', 'line4', 'line5', 'state', 'postcode', 'country']
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
    line1 = models.CharField("House No", max_length=255)
    line2 = models.CharField("Apartment Name", max_length=255, blank=True)
    line3 = models.CharField("Street Details", max_length=255, blank=True)
    line4 = models.CharField("Landmark", max_length=255, blank=True)
    line5 = models.CharField("City", max_length=255, blank=True)
    state = models.CharField("State/County", max_length=255, blank=True)
    postcode = UppercaseCharField("Post/Zip-code", max_length=64, blank=True)

    @property
    def house_no(self):
        return self.line1

    @property
    def apartment(self):
        return self.line2

    @property
    def street(self):
        return self.line3

    @property
    def landmark(self):
        return self.line4

    @property
    def city(self):
        return self.line5

    @apartment.setter
    def apartment(self, value):
        self.line2 = value

    @street.setter
    def street(self, value):
        self.line3 = value

    @landmark.setter
    def landmark(self, value):
        self.line4 = value

    @city.setter
    def city(self, value):
        self.line5 = value

    @property
    def summary_line(self):
        """
        Returns a single string summary of the address,
        separating fields using commas.
        """
        fields = ['line1', 'line2', 'line3', 'line4', 'line5', 'state', 'postcode', 'country']
        return ", ".join(self.get_field_values(fields))


class Line(AbstractLine):
    refunded_quantity = models.PositiveSmallIntegerField(default=0)

    @property
    def last_date_to__return(self):
        delta = datetime.timedelta(**settings.DEFAULT_PERIOD_OF_RETURN)
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


def clear_cache_order(sender, instance, **kwargs):
    cache.delete_pattern("apps.api_set_v2.views.orders?user={}&*".format(instance.user_id))


post_save.connect(clear_cache_order, sender=Order)


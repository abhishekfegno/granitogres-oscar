import datetime

from dateutil.utils import today
from django.contrib.gis.db.models import PointField
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db.models import Case
from django.db.models.signals import post_save
from django.utils.functional import cached_property, lazy
from oscar.apps.address.abstract_models import (
    AbstractBillingAddress, AbstractShippingAddress)
from oscar.apps.order.abstract_models import *

__all__ = ['PaymentEventQuantity', 'ShippingEventQuantity', 'Order']

from oscar.models.fields import UppercaseCharField

from apps.users.models import Location
from apps.utils.utils import get_statuses


def length_in_weeks(value):
    if 0 <= value <= 7:
        return value
    raise ValueError(f'day should be between 0 and 7')


class TimeSlotConfiguration(models.Model):
    start_time = models.TimeField(help_text="Delivery Time Starting of this slot")
    end_time = models.TimeField(help_text="(Expected) Delivery Time Ending of this slot")
    deliverable_no_of_orders = models.PositiveSmallIntegerField(help_text="No of Orders you can handle in this Slot! "
                                                                          "Each order will be at each location and "
                                                                          "will have diff size and no of items.")
    orders_prepare_delay = models.PositiveSmallIntegerField(
        help_text="This field specifies the time you want to prepare the orders! if your slot is 5PM-7PM, "
                  "and orders_prepare_delay=180minutes, Any orders placed after 2PM will not show this slot!")
    SUNDAY = 1
    MONDAY = 2
    TUESDAY = 3
    WEDNESDAY = 4
    THURSDAY = 5
    FRIDAY = 6
    SATURDAY = 7
    week_day_code = models.PositiveSmallIntegerField(choices=[
        (SUNDAY, "SUNDAY"),
        (MONDAY, "MONDAY"),
        (TUESDAY, "TUESDAY"),
        (WEDNESDAY, "WEDNESDAY"),
        (THURSDAY, "THURSDAY"),
        (FRIDAY, "FRIDAY"),
        (SATURDAY, "SATURDAY"),
    ], default=1, validators=[length_in_weeks])

    @property
    def index(self):
        h = self.start_time.hour
        m = self.start_time.minute
        s = self.start_time.second
        return self.week_day_code * (h * 60 * 60 + m * 60 + s)

    def clean(self):
        qs = self.__class__.objects.filter(week_day_code=self.week_day_code)
        if self.pk:
            qs = qs.filter(exclude=self.pk)
        for slot in qs:
            if slot.start_time < self.start_time < slot.end_time:
                raise ValidationError(f'start_time of this slot ({self.start_time}) conflicts with #{slot.id}. {slot}')
            if slot.end_time < self.end_time < slot.end_time:
                raise ValidationError(f'end_time of this slot ({self.end_time}) conflicts with #{slot.id}. {slot}')

    @property
    def week_day(self):
        return ['SUNDAY', 'MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY'][self.week_day_code]

    def __str__(self):
        return f"{self.start_time}-{self.end_time} {self.week_day}"

    @classmethod
    def indexed_config(cls):
        arr = []
        index = 1
        for config in cls.objects.all().order_by('week_day_code', 'start_time'):
            arr.append((index, config))
        return arr


class TimeSlot(models.Model):
    config = models.ForeignKey(TimeSlotConfiguration, on_delete=models.SET_NULL, null=True)
    slot = models.TextField(help_text="Text Representation of configuration")
    start_date = models.DateField(help_text="Delivery Starting Date")
    index = models.PositiveIntegerField(help_text="Slot Index")

    def __str__(self):
        return self.slot

    def __init__(self, *args, **kwargs):
        super(TimeSlot, self).__init__(*args, **kwargs)
        self.__orders = None

    @property
    def orders_assigned(self):
        if self.__orders is None:
            self.__orders = self.orders.all().count()
        return self.__orders

    @classmethod
    def free_slots(cls):
        return cls.objects.filter(
            start_date__gte=today(),
            config__deliverable_no_of_orders__gt=models.Count('orders')
        ).order_by('index')

    @classmethod
    def generate_next_n_slots(cls, n=5):
        time_now = datetime.datetime.now()
        slots_with_delivery_after_now = cls.objects.filter(
            start_date__gte=time_now.date(),
        ).annotate(
            orders_count=models.Count('orders')
        ).select_related('config').order_by('index')
        available_slots = [slot for slot in slots_with_delivery_after_now if slot.orders_count <= slot.config.deliverable_no_of_orders]
        latest_slot_date = available_slots[-1].start_date
        needed_slots = n - len(available_slots)
        configurations = TimeSlotConfiguration.indexed_config()
        configuration_index = 0
        out = []
        config = configurations[configuration_index][1]
        while needed_slots:
            dt = datetime.datetime(
                year=latest_slot_date.year, month=latest_slot_date.month, day=latest_slot_date.day,
                hour=config.start_time.hour, minute=config.start_time.minute, second=config.start_time.second,
            )
            slot, created = cls.objects.get_or_create(
                start_date=latest_slot_date,
                config=config,
                defaults={
                    'slot': f"{latest_slot_date} - {config.slot or ''}",
                    "index": int(datetime.datetime.timestamp(dt)) - 1625054000
                    # subtracting with timestamp at time of development to make index simpler
                }
            )
            if created:
                needed_slots -= 1
            configuration_index += 1
            if configuration_index >= len(configurations):
                configuration_index %= len(configurations)

            # if config.week_day_code != configurations[configuration_index][1].week_day_code:
            #     latest_slot_date =
            out.append(slot)


class Order(AbstractOrder):
    date_delivered = models.DateTimeField(null=True, blank=True, help_text="Date of Consignment Delivery")
    slot = models.ForeignKey(TimeSlot, on_delete=models.SET_NULL, null=True, related_name='orders')

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


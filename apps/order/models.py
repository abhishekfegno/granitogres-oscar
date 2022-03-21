import datetime
from threading import Lock

from dateutil.utils import today
from django.conf import settings
from django.contrib.gis.db.models import PointField
from django.core.cache import cache
from django.core.exceptions import ValidationError, MultipleObjectsReturned
from django.db.models import Case, PositiveSmallIntegerField, Prefetch
from django.db.models.signals import post_save
from django.utils import timezone
from django.utils.functional import cached_property, lazy
from oscar.apps.address.abstract_models import (
    AbstractBillingAddress, AbstractShippingAddress)
from oscar.apps.order.abstract_models import *
from oscar.apps.order.abstract_models import AbstractOrder
__all__ = ['PaymentEventQuantity', 'ShippingEventQuantity', 'Order']

from oscar.models.fields import UppercaseCharField

from apps.users.models import Location
from apps.utils.utils import get_statuses
from lib.exceptions import AlertException


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
        help_text="In Minutes. This field specifies the time you want to prepare the orders! if your slot is 5PM-7PM, "
                  "and orders_prepare_delay=180, (180 minutes) Any orders placed after 2PM will not show this slot!")
    is_active = models.BooleanField(default=True)
    index = models.PositiveIntegerField(default=0)

    SUNDAY = 1
    MONDAY = 2
    TUESDAY = 3
    WEDNESDAY = 4
    THURSDAY = 5
    FRIDAY = 6
    SATURDAY = 7
    week_day_code: int = models.PositiveSmallIntegerField(choices=[
        (SUNDAY, "SUNDAY"),
        (MONDAY, "MONDAY"),
        (TUESDAY, "TUESDAY"),
        (WEDNESDAY, "WEDNESDAY"),
        (THURSDAY, "THURSDAY"),
        (FRIDAY, "FRIDAY"),
        (SATURDAY, "SATURDAY"),
    ], default=1, validators=[length_in_weeks])

    def calc_index(self):
        return self.__class__._date_to_index(
            week=self.week_day_code, h=self.start_time.hour,
            m=self.start_time.minute, s=self.start_time.second
        )

    @classmethod
    def last_index(cls):
        return cls._date_to_index(week=cls.SATURDAY, h=23, m=59, s=59)

    @classmethod
    def _date_to_index(cls, week, h, m, s=0):
        return (week - 1) * 86400 + (h * 3600) + (m * 60) + s

    @classmethod
    def date_to_index(cls, dt):
        return cls._date_to_index(week=(dt.toordinal() % 7) + 1, h=dt.hour, m=dt.minute, s=dt.second)

    @classmethod
    def get_very_next_moment_slot(cls):
        """
        Next config slot
        """
        return cls.picked_index_config().first()

    def clean(self):
        qs = self.__class__.objects.filter(week_day_code=self.week_day_code)
        if self.pk:
            qs = qs.exclude(pk=self.pk)
        for slot in qs:
            if slot.start_time < self.start_time < slot.end_time:
                raise ValidationError(f'start_time of this slot ({self.start_time}) conflicts with #{slot.id}. {slot}')
            if slot.end_time < self.end_time < slot.end_time:
                raise ValidationError(f'end_time of this slot ({self.end_time}) conflicts with #{slot.id}. {slot}')

    @property
    def week_day(self):
        return ['SUNDAY', 'MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY'][self.week_day_code - 1]

    def __str__(self):
        return f"{self.start_time}-{self.end_time} {self.week_day}"

    @classmethod
    def indexed_config(cls):
        """
        Return Config QS In the order of Happening
        """
        return cls.objects.all().order_by('index')

    @classmethod
    def picked_index_config(cls, dt=None):
        """
        Will take a date as input, return an index config queryset in the order of very next Happening config first.
        ie: if dt is wednesday, 10:35 AM, qs will be sorted with the very next config on top. may be Wednesday 11:00 AM
        """
        if dt is None:
            dt = timezone.localtime(timezone.now())
        ind = cls.date_to_index(dt)
        filter_case = Case(
            models.When(index__gt=ind, then=models.Value(1)),
            default=models.Value(2),
            output_field=models.PositiveSmallIntegerField())
        return cls.objects.annotate(primary=filter_case).order_by('primary', 'index')

    def save(self, **kwargs):
        self.index = self.calc_index()
        return super(TimeSlotConfiguration, self).save(**kwargs)


class TimeSlot(models.Model):
    config = models.ForeignKey(TimeSlotConfiguration, on_delete=models.SET_NULL, null=True)
    slot = models.TextField(help_text="Text Representation of configuration")
    start_date = models.DateField(help_text="Delivery Starting Date")
    index = models.BigIntegerField(help_text="Slot Index")

    __timeslot_generator_concurrency_lock = Lock()

    def __str__(self):
        return self.slot

    def __init__(self, *args, **kwargs):
        super(TimeSlot, self).__init__(*args, **kwargs)
        self.__orders = None

    def to_dict(self, is_next=False):
        return {
                'pk': self.pk,
                'start_time': self.config.start_time.strftime("%-I:%M %p"),
                'end_time': self.config.end_time.strftime("%-I:%M %p"),
                'start_date': self.start_date.strftime("%-d %b, %Y"),
                'day': self.start_date.strftime('%A'),
                'max_datetime_to_order': self.max_datetime_to_order,
                'is_next': is_next,
                'index': self.index,
            }

    def clean(self):
        if not self.config:
            raise ValidationError('Config is Required')
        if ((self.start_date.toordinal() % 7) + 1) != self.config.week_day_code:
            raise ValidationError('Timeslot Date does not match with Config Weekday')

    def save(self, **kwargs):
        if ((self.start_date.toordinal() % 7) + 1) != self.config.week_day_code:
            raise ValidationError('Timeslot Date does not match with Config Weekday')
        self.slot = f'{str(self.config)} {self.start_date}'
        super(TimeSlot, self).save(**kwargs)

    @property
    def orders_assigned(self):
        if self.__orders is None:
            self.__orders = self.orders.all().count()
        return self.__orders

    _free_slot_qs = ...

    @classmethod
    def append_free_slot(cls, slot):
        slot.ord_count = 0
        # if cls._free_slot_qs
        cls._free_slot_qs = ...          #.append(slot)

    @classmethod
    def free_slots(cls, force=False):
        """
        Slots that are free for delivery
        """
        if cls._free_slot_qs is ...:
            cls._free_slot_qs = cls.objects.annotate(ord_count=models.Count('orders')).filter(
                start_date__gte=today(),
                config__is_active=True,
                config__deliverable_no_of_orders__gt=models.F('ord_count'),
            ).prefetch_related(Prefetch('config')).order_by('index')

        return cls._free_slot_qs

    @property
    def max_datetime_to_order(self):
        """
        Maximum datetime before which one can order to this
        """
        starting_dt = self.order_starting_datetime

        return starting_dt - datetime.timedelta(minutes=self.config.orders_prepare_delay + 1)

    @classmethod
    def next_slot_from_request(cls, request):

        return cls.next_slot()

    @classmethod
    def next_slot(cls, ):
        slots = TimeSlot.get_upcoming_slots()
        slots_ = [slot.to_dict(is_next=index == 0) for index, slot in enumerate(slots)]
        return slots_

    @classmethod
    def upcoming_slots_for_request(cls, request):

        return cls.get_upcoming_slots()

    @property
    def order_starting_datetime(self):
        return timezone.make_aware(datetime.datetime(
            year=self.start_date.year, month=self.start_date.month, day=self.start_date.day,
            hour=self.config.start_time.hour, minute=self.config.start_time.minute,
            second=self.config.start_time.second,
        ), timezone.get_default_timezone())

    @classmethod
    def slots_available_for_delivery(cls, n, force=False):
        """
        Deliverable slots which are capable to hold more orders after now!
        """
        time_now = timezone.localtime(timezone.now())
        slots = [slot for slot in cls.free_slots(force=force) if (slot.max_datetime_to_order > time_now)]
        return slots

    @classmethod
    def get_upcoming_slots(cls, n=settings.MINIMUM_TIMESLOT_TO_BE_PROVIDED):
        """
        Fetching all already prepared slot!
        """

        """some of the intermediate slots might become over booked. so we are picking only available slots"""
        return []
        available_slots = cls.slots_available_for_delivery(n, force=True)
        needed_slots: int = n - len(available_slots)  # so we needed {needed_slots} more slots.
        print(f"""so we need {needed_slots} slots more.""")  # docstring
        if needed_slots <= 0:
            print("All slots are available in  DB.")
            return available_slots
        print("waiting for lock")
        if cls.__timeslot_generator_concurrency_lock.acquire(blocking=False):        # max timeout 5 seconds
            """
            Locking the scenario so that only one request can generate slots at a time.
            using threading.Lock() for that.
            refer: https://docs.python.org/3/library/threading.html#threading.Lock.acquire
            """
            print("lock aquired")
            """We need to generate more slots. So lets pickup all the slots regardless of they are filled or not."""
            print('... all_slots')
            all_slots = cls.free_slots()     # so we needed {needed_slots} more slots.
            print('... latest_slot')
            latest_slot = list(all_slots)[-1] if all_slots else None
            if latest_slot:
                curr_date = latest_slot.start_date
            else:
                curr_date = today()
            print('... curr_date')
            config_index = 0

            configurations = list(TimeSlotConfiguration.picked_index_config())
            print('... got configurations')
            if len(configurations) == 0:
                cls.__timeslot_generator_concurrency_lock.release()
                raise Exception(f"No Slot Configurations has been set. please create one ")

            # needed_slots = 5

            while needed_slots > 0:
                """Planning to generate each slot as required."""
                print(f'...... {needed_slots} > inloop')
                config = configurations[config_index % len(configurations)]
                print(f'...... {needed_slots} > got config')
                config_index += 1
                has_config = lambda slot: slot.config == config and slot.start_date >= curr_date

                print(f'...... {needed_slots} > got has_config={has_config}')
                # if not all(filter(has_config, all_slots)):
                curr_week_day: int = (curr_date.toordinal() % 7) + 1
                week_sum = int(config_index // len(configurations)) * 7
                days_to_next_slot: int = config.week_day_code - curr_week_day + week_sum
                print(f'...... {needed_slots} > has config for some thing')

                dt = datetime.datetime(
                    year=curr_date.year, month=curr_date.month, day=curr_date.day,
                    hour=config.start_time.hour, minute=config.start_time.minute, second=config.start_time.second,
                ) + datetime.timedelta(days=days_to_next_slot)

                print(f'...... {needed_slots} > dt={dt}')
                # subtracting with timestamp at time of development to make index simpler
                index = (datetime.datetime.timestamp(dt)) - 1625054000
                slot = f"{dt} - {str(config)}"
                start_date = dt.date()

                try:
                    latest_slot, created = cls.objects.get_or_create(
                        start_date=start_date,
                        config=config,
                        defaults={
                            'slot': slot,
                            "index": index
                        }
                    )
                    print(f'...... {needed_slots} > try >  latest_slot={latest_slot}, created={created}')

                    # cls._free_slot_qs = ...     # reseting __free_slot_qs
                    if created:
                        print("Generated New ", latest_slot)
                    else:
                        print("Acquiring slot from db", latest_slot)
                except MultipleObjectsReturned as more:
                    print(
                        more,
                        f"\n>>> Multiple slots returned while trying to generate "
                        f"TimeSlot(start_date=<{start_date}>, config=<{config}>)",
                    )         # error
                    latest_slot = cls.objects.filter(start_date=start_date, config=config).last()
                    print("Acquiring slot from db", latest_slot)
                    cls.objects.filter(start_date=start_date, config=config).exclude(pk=latest_slot.pk).delete()
                    created = False
                cls.append_free_slot(latest_slot)
                curr_date = latest_slot.start_date

                if created:
                    needed_slots -= 1
                    if needed_slots <= 0:
                        print(f'...... {needed_slots} > created >  breaking')
                        break
                # else:
                #     print('aaaaaaaaa')
                #     print(has_config, all_slots, [(has_config(c)) for c in all_slots])
            cls.__timeslot_generator_concurrency_lock.release()
            print("lock released")
        else:
            print("cant access lock even after timeout")
        return cls.slots_available_for_delivery(n)


class Order(AbstractOrder):
    date_delivered = models.DateTimeField(null=True, blank=True, help_text="Date of Consignment Delivery")
    slot = models.ForeignKey(TimeSlot, on_delete=models.SET_NULL, null=True, related_name='orders')
    pickup = models.ForeignKey('delhivery.RequestPickUp', null=True, blank=True, on_delete=models.SET_NULL,
                               related_name='delhivery_consignments')
    waybill = models.CharField(null=True, max_length=64)

    @property
    def date_placed_date(self):
        return self.date_placed.date()

    @property
    def get_product(self):
        products = ""
        for i in self.lines.all().values_list('product__title'):
            products += i[0]+","
        return products

    @property
    def get_costlier(self):
        return self.lines.all().order_by('-unit_price_incl_tax').first().title

    def payment_type_for_delhivery(self):
        # Prepaid / COD / Pickup / REPL
        if self.status in dict(settings.OSCAR_ADMIN_POSSIBLE_LINE_STATUSES_AFTER_DELIVERY).keys():
            return "Pickup"
        from apps.payment.models import Source
        s = Source.objects.filter(order=self).last()
        from apps.payment.utils.cash_payment import Cash
        if s.source_type == Cash.name:
            return 'COD'
        return 'Prepaid'

    @property
    def shipping_description(self):
        return f"{self.num_lines} items from Chikaara Cosmetics against Order #{self.number} "

    def _create_order_status_change(self, old_status, new_status):
        # Not setting the status on the order as that should be handled before
        self.status_changes.create(old_status=old_status, new_status=new_status, date_created=self.date_placed)

    @property
    def preferred_slot_text(self):
        return self.slot and self.slot.slot

    @property
    def is_cancelable(self):
        return self.status in settings.OSCAR_USER_CANCELLABLE_ORDER_STATUS

    @property
    def max_time_to__return(self):
        delta = datetime.timedelta(**settings.DEFAULT_PERIOD_OF_RETURN)
        return self.delivery_time and (self.delivery_time + delta)

    @property
    def is_return_time_expired(self):
        return not self.delivery_time or (
                self.max_time_to__return and bool(self.max_time_to__return < timezone.localtime(timezone.now())))

    @cached_property
    def delivery_time(self):
        if self.status in get_statuses(775):
            return None  # as the package is not delivered
        if not self.date_delivered:
            date_delivered = self.status_changes.filter(new_status=settings.ORDER_STATUS_DELIVERED).order_by(
                'date_created').first()
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
        return bool(self.last_date_to__return >= timezone.localtime(timezone.now()))

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

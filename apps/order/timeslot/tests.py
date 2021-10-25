from django.test import TestCase
from django.utils.datetime_safe import time

from apps.order.models import TimeSlotConfiguration, TimeSlot


class TimeSlotConfigurationTest(TestCase):

    def setUp(self):
        self.data_set = [
            # Monday
            TimeSlotConfiguration(
                start_time=time(hour=10, minute=30), end_time=time(hour=12, minute=00),
                deliverable_no_of_orders=5, orders_prepare_delay=120, week_day_code=TimeSlotConfiguration.MONDAY),
            TimeSlotConfiguration(
                start_time=time(hour=14, minute=30), end_time=time(hour=16, minute=30),
                deliverable_no_of_orders=10, orders_prepare_delay=180, week_day_code=TimeSlotConfiguration.MONDAY),
            TimeSlotConfiguration(
                start_time=time(hour=17, minute=30), end_time=time(hour=19, minute=30),
                deliverable_no_of_orders=30, orders_prepare_delay=180, week_day_code=TimeSlotConfiguration.MONDAY),

            # Tuesday
            TimeSlotConfiguration(
                start_time=time(hour=10, minute=30), end_time=time(hour=12, minute=00),
                deliverable_no_of_orders=5, orders_prepare_delay=120, week_day_code=TimeSlotConfiguration.TUESDAY),
            TimeSlotConfiguration(
                start_time=time(hour=14, minute=30), end_time=time(hour=16, minute=30),
                deliverable_no_of_orders=10, orders_prepare_delay=180, week_day_code=TimeSlotConfiguration.TUESDAY),
            TimeSlotConfiguration(
                start_time=time(hour=17, minute=30), end_time=time(hour=19, minute=30),
                deliverable_no_of_orders=20, orders_prepare_delay=180, week_day_code=TimeSlotConfiguration.TUESDAY),

            # Wednesday
            TimeSlotConfiguration(
                start_time=time(hour=11, minute=30), end_time=time(hour=14, minute=30),
                deliverable_no_of_orders=10, orders_prepare_delay=180, week_day_code=TimeSlotConfiguration.WEDNESDAY),
            TimeSlotConfiguration(
                start_time=time(hour=18, minute=00), end_time=time(hour=21, minute=00),
                deliverable_no_of_orders=20, orders_prepare_delay=180, week_day_code=TimeSlotConfiguration.WEDNESDAY),

            # Thursday
            TimeSlotConfiguration(
                start_time=time(hour=10, minute=30), end_time=time(hour=12, minute=00),
                deliverable_no_of_orders=5, orders_prepare_delay=120, week_day_code=TimeSlotConfiguration.THURSDAY),
            TimeSlotConfiguration(
                start_time=time(hour=14, minute=30), end_time=time(hour=16, minute=30),
                deliverable_no_of_orders=10, orders_prepare_delay=180, week_day_code=TimeSlotConfiguration.THURSDAY),
            TimeSlotConfiguration(
                start_time=time(hour=17, minute=30), end_time=time(hour=19, minute=30),
                deliverable_no_of_orders=20, orders_prepare_delay=180, week_day_code=TimeSlotConfiguration.THURSDAY),

            # Friday
            TimeSlotConfiguration(
                start_time=time(hour=10, minute=30), end_time=time(hour=12, minute=00),
                deliverable_no_of_orders=5, orders_prepare_delay=120, week_day_code=TimeSlotConfiguration.FRIDAY),
            TimeSlotConfiguration(
                start_time=time(hour=14, minute=30), end_time=time(hour=16, minute=30),
                deliverable_no_of_orders=10, orders_prepare_delay=180, week_day_code=TimeSlotConfiguration.FRIDAY),
            TimeSlotConfiguration(
                start_time=time(hour=17, minute=30), end_time=time(hour=19, minute=30),
                deliverable_no_of_orders=20, orders_prepare_delay=180, week_day_code=TimeSlotConfiguration.FRIDAY),

            # Saturday
            TimeSlotConfiguration(
                start_time=time(hour=9, minute=30), end_time=time(hour=11, minute=00),
                deliverable_no_of_orders=5, orders_prepare_delay=120, week_day_code=TimeSlotConfiguration.SATURDAY),
            TimeSlotConfiguration(
                start_time=time(hour=12, minute=30), end_time=time(hour=13, minute=30),
                deliverable_no_of_orders=10, orders_prepare_delay=180, week_day_code=TimeSlotConfiguration.SATURDAY),
            TimeSlotConfiguration(
                start_time=time(hour=15, minute=00), end_time=time(hour=16, minute=00),
                deliverable_no_of_orders=20, orders_prepare_delay=180, week_day_code=TimeSlotConfiguration.SATURDAY),
            TimeSlotConfiguration(
                start_time=time(hour=17, minute=30), end_time=time(hour=19, minute=30),
                deliverable_no_of_orders=10, orders_prepare_delay=180, week_day_code=TimeSlotConfiguration.SATURDAY),
        ]
        self.data_set = TimeSlotConfiguration.objects.bulk_create(self.data_set)
        for dt in TimeSlotConfiguration.objects.all():
            dt.save()

    def deprecated_test_get_upcoming_slots(self):
        conf = TimeSlotConfiguration.get_very_next_moment_slot()
        self.assertEqual(conf.start_time.hour, 11, "Hour Mismatch")     # 2:30
        self.assertEqual(conf.week_day_code, 4, "Day Mismatch")     # tuesday

        slots = TimeSlot.get_upcoming_slots(n=3)
        self.assertGreaterEqual(len(slots), 3, msg="Could not Create required Slots for first time.")
        for slot in slots:
            self.assertLess(slot.orders_assigned, slot.config.deliverable_no_of_orders, "Found some slots without")
        slots = TimeSlot.get_upcoming_slots(n=5)
        self.assertGreaterEqual(len(slots), 5, msg="Could not Create required Slots for first time.")
        for slot in slots:
            self.assertLess(slot.orders_assigned, slot.config.deliverable_no_of_orders, "Found some slots without")

        slots = TimeSlot.get_upcoming_slots(n=8)
        self.assertGreaterEqual(len(slots), 5, msg="Could not Create required Slots for first time.")
        for slot in slots:
            self.assertLess(slot.orders_assigned, slot.config.deliverable_no_of_orders, "Found some slots without")

        slots = TimeSlot.get_upcoming_slots(n=25)
        self.assertGreaterEqual(len(slots), 5, msg="Could not Create required Slots for first time.")
        for slot in slots:
            self.assertLess(slot.orders_assigned, slot.config.deliverable_no_of_orders, "Found some slots without")


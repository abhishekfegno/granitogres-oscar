from django.core.management import BaseCommand

from apps.order.models import TimeSlotConfiguration, TimeSlot


class Command(BaseCommand):

    def assertEqual(self, a, b, msg):
        assert a == b, '{} == {}, {}'.format(a, b, msg)

    def assertGreaterEqual(self, a, b, msg):
        assert a >= b, '{} >= {}, {}'.format(a, b, msg)

    def assertLess(self, a, b, msg):
        assert a < b, '{} < {}, {}'.format(a, b, msg)

    def handle(self, *args, **options):
        conf = TimeSlotConfiguration.get_very_next_moment_slot()
        self.assertEqual(conf.start_time.hour, 11, "Hour Mismatch")  # 2:30
        self.assertEqual(conf.week_day_code, 4, "Day Mismatch")  # tuesday

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
        print(slots)
        print("****************************")
        slots = TimeSlot.get_upcoming_slots(n=25)
        self.assertGreaterEqual(len(slots), 5, msg="Could not Create required Slots for first time.")
        for slot in slots:
            self.assertLess(slot.orders_assigned, slot.config.deliverable_no_of_orders, "Found some slots without")


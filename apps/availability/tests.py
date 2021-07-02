from datetime import datetime

from django.test import TestCase

from apps.order.models import TimeSlot


class TimeSlotTest(TestCase):

    def setUp(self):
        dataset = [{
            'start_time': datetime.time(hour=10, minute=00)
        },
        ]
        TimeSlot.objects.create(name="lion", sound="roar")
        TimeSlot.objects.create(name="cat", sound="meow")

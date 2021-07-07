from django.core.management.base import BaseCommand
from django.utils.datetime_safe import time

from apps.order.models import TimeSlotConfiguration


class Command(BaseCommand):
    help = "My shiny new management command."

    # def add_arguments(self, parser):
    #     parser.add_argument('sample', nargs='+')

    def handle(self, *args, **options):
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
        TimeSlotConfiguration.objects.bulk_create(self.data_set)

        for dt in TimeSlotConfiguration.objects.all():
            dt.save()


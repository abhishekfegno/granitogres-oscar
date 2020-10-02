from django.core.management.base import BaseCommand

from apps.payment.models import Source


class Command(BaseCommand):
    help = "Fix Sources."

    # def add_arguments(self, parser):
    #     parser.add_argument('sample', nargs='+')

    def handle(self, *args, **options):
        fixed = 0
        total = 0

        for source in Source.all.all():
            total += 1
            if source.order.total_incl_tax != source.amount_allocated:
                fixed += 1
                source.is_active = False
                source.save()
                print(str(source), "Fixed!")
        print(f"Fixed {fixed} out of {total} issues!")

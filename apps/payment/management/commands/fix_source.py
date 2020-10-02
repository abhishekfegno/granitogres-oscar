from collections import defaultdict

from django.core.management.base import BaseCommand

from apps.payment.models import Source


class Command(BaseCommand):
    help = "Fix Sources."

    # def add_arguments(self, parser):
    #     parser.add_argument('sample', nargs='+')

    def handle(self, *args, **options):
        fixed = 0
        total = 0
        sources_with_same_rate = defaultdict(list)
        for source in Source.all.filter():
            total += 1
            if source.order.total_incl_tax != source.amount_allocated:
                fixed += 1
                source.is_active = False
                source.save()
                print(str(source), "Fixed!")
            else:
                sources_with_same_rate[source.order].append(source)
        for order, sources in sources_with_same_rate.items():
            master = sources and sources[:1]
            slaves = sources[1:]
            for slave in slaves:
                slave.is_active = False
                slave.save()

        print(f"Fixed {fixed} out of {total} issues!")

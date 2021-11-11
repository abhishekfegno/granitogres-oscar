import csv

from django.core.management import BaseCommand

from apps.catalogue.models import Product, ProductAttribute


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('pc', help='Product Class ID from DB')

    def handle(self, *args, **options):
        out = []

        pa = ProductAttribute.objects.filter(product_class=options['pc']).values_list('code', flat=True)
        for p in Product.objects.all().filter(product_class=options['pc']).prefetch_related('attributes'):
            dataset = {
                'id': p.id,
                'name': p.title,
                'structure': p.structure,
                'parent_id': p.parent_id,
            }
            for _attr_code in pa:
                dataset[_attr_code] = ''
                if hasattr(p.attr, _attr_code):
                    dataset[_attr_code] = getattr(p.attr, _attr_code)
            out.append(dataset)

        print("Writing to sheet :: ", f'public/dataset/export/{options["pc"]}.csv')
        with open(f'public/dataset/export/{options["pc"]}.csv', 'w', newline='') as csvfile:
            fieldnames = ['id', 'name', *[_attr_code for _attr_code in pa]]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(out)
            print("Written!")




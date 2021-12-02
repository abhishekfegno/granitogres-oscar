import csv
import os

from django.core.management import BaseCommand
from apps.catalogue.models import Product, ProductAttribute
from lib.product_utils.filter import ProductClass


class Command(BaseCommand):

    def handle(self, *args, **options):
        for pc in ProductClass.objects.all():
            out = []
            pa = ProductAttribute.objects.filter(product_class=pc).values_list('code', flat=True)
            for p in Product.objects.all().filter(product_class=pc).prefetch_related('attributes'):
                cat = p.categories.all().first()
                dataset = {
                    'id': p.id,
                    'name': p.title,
                    'structure': p.structure,
                    'parent_id': p.parent_id,
                    'category': cat.full_name if cat else '',
                    'brand': p.brand and p.brand.name,
                }
                for _attr_code in pa:
                    dataset[_attr_code] = ''
                    if hasattr(p.attr, _attr_code):
                        dataset[_attr_code] = getattr(p.attr, _attr_code)
                out.append(dataset)
            os.mkdir('public/dataset/export-dec2/')
            print("Writing to sheet :: ", f'public/dataset/export-dec2/{pc.slug}.csv')
            with open(f'public/dataset/export-nov25/{pc.slug}.csv', 'w', newline='') as csvfile:
                fieldnames = ['id', 'name', 'structure', 'parent_id', 'category', 'brand',  *[_attr_code for _attr_code in pa]]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(out)
                print("Written!")




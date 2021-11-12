import csv
from django.core.management import BaseCommand
from apps.catalogue.models import Product, ProductAttribute, ProductAttributeValue
from lib.product_utils.filter import ProductClass


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('path', type=str, help='please choose a path of dataset')

    def handle(self, *args, **kwargs):
        print(kwargs)
        with open(kwargs['path'], 'r') as data:
            dataset = csv.DictReader(data) # getting csv data as dict

            for row in dataset:
                p = Product.objects.filter(pk=row['id'])[0] # get or create each product from the the sheet
                p, _ = Product.objects.get_or_create(pk=row[id])
                # pa = ProductAttribute.objects.filter(product_class=p.product_class).values_list('code', flat=True)
                pav = ProductAttributeValue.object.filter(product=p) # getting corresponding ProductAttributeValue of Product
                row_keys = [row.pop(i, None) for i in ['id', 'name', 'structure', 'parent_id']] #removing keys other than PAV keys
                for field in row.keys():
                    if hasattr(p.attr, field): # if product has the field as attribute
                        for i in pav:
                            if i.attribute.name == field.upper(): # from each tester
                                i.value_text = row[field]
                                print(i.value_text)

                                i.save()
                    else:
                        print(f"{p} has no such attribute { field }")
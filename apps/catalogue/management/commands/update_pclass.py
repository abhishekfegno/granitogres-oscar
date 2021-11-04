import csv
import os.path
from typing import Union

from django.core.management import BaseCommand
from apps.catalogue.models import ProductClass, Product
from oscar.core.utils import slugify

from apps.catalogue.models import ProductAttribute


def _slugify(val):
    return slugify(val).replace('-', '_')

pc_list = ProductClass.objects.all().prefetch_related('attributes')


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('path', type=str, help='please choose the csv file')
        parser.add_argument('json_data', type=str, help='please choose the json file')

    def extract_product_class_from_row(self, row) -> ProductClass:
        name = row['NEW GROUP']
        attrs = row['Attributes'].split(',')
        pclass = None
        is_created = False
        for obj in pc_list:
            if name == obj.name:
                pclass = obj
                is_created = False
                break
        if pclass is None:
            pclass = ProductClass.objects.create(name=name, slug=_slugify(name))
            is_created = True
            print(pclass, is_created)
        db_attrs = pclass.attributes.all().values_list('name', flat=True)
        remaining_attrs = set(attrs).difference(set(db_attrs))
        objects = []

        if remaining_attrs:
            for attr in remaining_attrs:
                objects.append(ProductAttribute(
                    name=attr, code=_slugify(attr),
                    product_class=pclass,
                    type=ProductAttribute.TEXT, required=False, is_varying=True))
                if attr.lower() == "color":
                    objects.append(ProductAttribute(
                        name="HexColor", code="hexcolor",
                        product_class=pclass,
                        type=ProductAttribute.COLOR, required=False, is_varying=True))
        if objects:
            ProductAttribute.objects.bulk_create(objects)
        db_attrs = pclass.attributes.all().values_list('name', flat=True)

        for _id in range(1, 4):
            attr = row.get(f'Attr{_id}-name').strip()
            if attr and attr not in db_attrs:
                val = row.get(f'Attr{_id}-value')
                in_filter = row.get(f'Attr{_id}-infilter')
                in_attribute = row.get(f'Attr{_id}-inattribute')
                pa, created = ProductAttribute.objects.get_or_create(
                    name=attr, code=_slugify(attr),
                    product_class=pclass,
                    type=ProductAttribute.TEXT, required=False, is_varying=in_filter == 'TRUE'
                )
                db_attrs = list(db_attrs) + [attr]

                print(pclass, attr, val, row['Product ID'], created)
        return pclass

    def get_product(self, row) -> Product:
        product = Product.objects.filter(id=row['Product ID']).first()
        return product

    def update_product_from_row(self, product: Product, row: list, product_class: ProductClass, ) -> Union[None, Product]:
        if not product:
            print("Skipping Product Update..........")
            return
        if product.is_child:
            product.product_class = None
            product.parent.product_class = product_class
            product.parent.save()
        else:
            product.product_class = product_class
        product.save()
        return product

    def handle(self, *args, **options):
        path = options['path']
        json_data = options['json_data']
        if not os.path.exists(path):
            print("Cant access file ", path)
            return

        with open(path) as csvfile:
            row_reader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
            for row in row_reader:
                p_class = self.extract_product_class_from_row(row)
                product = self.update_product_from_row(self.get_product(row), row, p_class)




import csv
import json
import os.path
from typing import Union

from django.core.management import BaseCommand
from oscar.apps.catalogue.models import AttributeOptionGroup, AttributeOption

from apps.catalogue.models import ProductClass, Product, ProductAttributeValue
from oscar.core.utils import slugify

from apps.catalogue.models import ProductAttribute


def _slugify(val):
    return slugify(val).replace('-', '_')

pc_list = ProductClass.objects.all().prefetch_related('attributes')

probable_filterable_attribute_text = [
    'Material', 'Brand Name', 'Material', 'Color', 'HexColor', 'Room Type', 'Brand', 'Finish', 'Thickness',  'Trap Type', 'Trap Size',
]
probable_filterable_attribute_bool = [
    'Syphonic', 'Rimless',
]


class Command(BaseCommand):

    def __init__(self):
        super().__init__()
        self.initial_p_class = {}
        self.initial_product = {}

    def add_arguments(self, parser):
        parser.add_argument('path', type=str, help='please choose the csv file')
        parser.add_argument('json_data', type=str, help='please choose the json file')

    def extract_product_class_from_row(self, row) -> ProductClass:
        name = row['NEW GROUP']
        if name in self.initial_p_class and self.initial_p_class.get('name'):
            return self.initial_p_class['name']
        slug = _slugify(name)
        p_class = None
        is_created = False
        for obj in pc_list:
            if name == obj.name:
                p_class = obj
                is_created = False
                break
        if p_class is None:
            p_class, is_created = ProductClass.objects.get_or_create(slug=slug, defaults={"name": name})
            print(p_class, is_created)

        # attrs = row['Attributes'].strip().split(',')
        # db_attrs = pclass.attributes.all().values_list('name', flat=True)
        # remaining_attrs = set(attrs).difference(set(db_attrs))
        # objects = []
        #
        # if remaining_attrs:
        #     for attr in remaining_attrs:
        #         objects.append(ProductAttribute(
        #             name=attr, code=_slugify(attr),
        #             product_class=pclass,
        #             type=ProductAttribute.TEXT, required=False, is_varying=True))
        #         if attr.lower() == "color":
        #             objects.append(ProductAttribute(
        #                 name="HexColor", code="hexcolor",
        #                 product_class=pclass,
        #                 type=ProductAttribute.COLOR, required=False, is_varying=True))
        # if objects:
        #     ProductAttribute.objects.bulk_create(objects)
        # db_attrs = pclass.attributes.all().values_list('name', flat=True)
        #
        # for _id in range(1, 4):
        #     attr = row.get(f'Attr{_id}-name').strip()
        #     if attr and attr not in db_attrs:
        #         val = row.get(f'Attr{_id}-value')
        #         in_filter = row.get(f'Attr{_id}-infilter')
        #         in_attribute = row.get(f'Attr{_id}-inattribute')
        #         pa, created = ProductAttribute.objects.get_or_create(
        #             name=attr, code=_slugify(attr),
        #             product_class=pclass,
        #             type=ProductAttribute.TEXT, required=False, is_varying=in_filter == 'TRUE'
        #         )
        #         db_attrs = list(db_attrs) + [attr]
        #
        #         print(pclass, attr, val, row['Product ID'], created)
        self.initial_p_class[name] = p_class

        return p_class

    def get_product(self, row) -> Product:
        # if row['Product ID'] in self.initial_product:
        #     return self.initial_product[row['Product ID']]
        product = Product.objects.filter(id=row['Product ID']).select_related('product_class').first()
        # self.initial_product[row['Product ID']] = product
        return product

    def update_product_class_from_row(self, product: Product, row: list, product_class: ProductClass, ) -> Union[None, Product]:
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
        print("Updated Product........")
        return product

    def handle(self, *args, **options):
        path = options['path']
        json_file = options['json_data']
        if not os.path.exists(path):
            print("Cant access file ", path)
            return
        if not os.path.exists(json_file):
            print("Cant access file ", json_file)
            return

        # ProductAttributeValue.objects.all().delete()
        # AttributeOptionGroup.objects.all().delete()
        # AttributeOption.objects.all().delete()
        # AttributeOption.objects.all().delete()
        # ProductAttribute.objects.all().delete()

        with open(path) as csvfile_pointer:
            row_reader = csv.DictReader(csvfile_pointer, delimiter=',', quotechar='"')
            for row in row_reader:
                p_class = self.extract_product_class_from_row(row)
                product = self.update_product_class_from_row(self.get_product(row), row, p_class)
                print(
                    "PClass Name: " + row['NEW GROUP'],
                    "PClass Name@DB", p_class,
                    "Product ID: " + row['Product ID'],
                    "Product Name@DB: ", product and product.pk)
        with open(json_file) as jsonfile_pointer:
            json_data = json.load(jsonfile_pointer)
            for attribute_data in json_data:
                self.update_product_attribute(attribute_data)

    def attr_type_descriptor(
            self,
            attribute__name=None, value_text=None, value_image=None,
            value_color=None, product_id=None, attribute__code=None
    ):
        """
        return ( field_type, should_show_in_filter, should_show_in_attributes_selector )
        """
        if value_text and len(value_text.split(' ')) > 3:
            return ProductAttribute.RICHTEXT, False, True
        if value_color:
            return ProductAttribute.COLOR, False, True
        if attribute__name in probable_filterable_attribute_text:
            return ProductAttribute.TEXT, True, True
        if attribute__name in probable_filterable_attribute_bool:
            return ProductAttribute.BOOLEAN, True, True
        if attribute__name in probable_filterable_attribute_bool:
            return ProductAttribute.BOOLEAN, True, True
        return ProductAttribute.TEXT, True, False

    def update_product_attribute(self, attr):
        """
          {
            "product_id": 4423,
            "attribute__name": "Salient Feature",
            "attribute__code": "salient_feature",
            "value_text": "Anti Corrosive and Easy to Clean..",
            "value_color": null,
            "value_image": ""
          },
        """

        fake_row = {'Product ID': attr['product_id']}
        product = self.get_product(fake_row)
        if not product:
            return
        field_type, add_to_filter, add_to_attribute = self.attr_type_descriptor(**attr)
        if not hasattr(product.attr, attr['attribute__code']):
            if product.is_child:
                product.parent.refresh_from_db(fields=('product_class', ))
            else:
                product.refresh_from_db(fields=('product_class',))
            p_class = product.get_product_class()
            print("Creating ", attr['attribute__name'], "For", p_class)
            p_class.attributes.create(
                product_class=p_class,
                name=attr['attribute__name'],
                code=attr['attribute__code'],
                type=field_type,
                is_varying=add_to_attribute,
                is_visible_in_filter=add_to_filter
            )
        print("Updating attribte")
        value = attr['value_text'] or attr['value_color'] or attr['value_image']
        setattr(product.attr, attr['attribute__code'], value)














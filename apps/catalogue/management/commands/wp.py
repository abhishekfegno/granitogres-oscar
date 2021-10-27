import uuid

import psycopg2
from django.core.management import BaseCommand
import csv

from django.db import models, IntegrityError
from django.utils.text import slugify

import urllib3
from typing import Optional
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from apps.catalogue.models import ProductClass, ProductAttributeValue

from apps.catalogue.models import Product, Category, ProductImage, ProductAttribute, Brand
from apps.partner.models import Partner, StockRecord


def fetch_image(url: str, instance: models.Model, field: str, name: Optional[str] = None):
    try:
        print(url)
        conn = urllib3.PoolManager()
        img_temp = NamedTemporaryFile(delete=True)
        img_temp.flush()
        img_temp.write(conn.request('GET', url).data)
        img_temp.flush()
        img_format = url.split('.')[-1]
        if name is None:
            name = url.split('/')[-1]
        if not name.endswith(img_format):
            name += f'.{img_format}'
        (getattr(instance, field)).save(name, File(img_temp))
        print((getattr(instance, field)).url)
        print(instance)
    except Exception as e:
        print(e)
        print(url, instance, field, name)
    return instance


def digit(val):

    if type(val) in (float, int):
        return val
    if type(val) is str and val.isdigit():
        return float(val)
    return 0.0


class Command(BaseCommand):
    """
    ./manage.py load_from_wordpress public/dataset/abchauz_wp/wc-product-export-24-8-2021-1629795340224.csv
    HEADER:
    ID,
    Type,
    SKU,
    Name,
    Published,
    "Is featured?",
    "Visibility in catalog",
    "Short description",
    Description,
    "Date sale price starts",
    "Date sale price ends",
    "Tax status",
    "Tax class",
    "In stock?",
    Stock,
    "Low stock amount",
    "Backorders allowed?",
    "Sold individually?",
    "Weight (kg)",
    "Length (mm)",
    "Width (mm)",
    "Height (mm)",
    "Allow customer reviews?",
    "Purchase note",
    "Sale price",
    "Regular price",
    Categories,Tags,
    "Shipping class",
    Images,
    "Download limit",
    "Download expiry days",
    Parent,
    "Grouped products",
    Upsells,
    Cross-sells,
    "External URL",
    "Button text",
    Position,
    "Attribute 1 name",
    "Attribute 1 value(s)",
    "Attribute 1 visible",
    "Attribute 1 global",
    "Attribute 2 name",
    "Attribute 2 value(s)",
    "Attribute 2 visible",
    "Attribute 2 global",
    "Attribute 3 name",
    "Attribute 3 value(s)",
    "Attribute 3 visible",
    "Attribute 3 global",
    "Attribute 3 default",
    "Attribute 4 name",
    "Attribute 4 value(s)",
    "Attribute 4 visible",
    "Attribute 4 global",
    "Attribute 5 name",
    "Attribute 5 value(s)",
    "Attribute 5 visible",
    "Attribute 5 global",
    "Attribute 6 name",
    "Attribute 6 value(s)",
    "Attribute 6 visible",
    "Attribute 6 global",
    "Attribute 7 name",
    "Attribute 7 value(s)",
    "Attribute 7 visible",
    "Attribute 7 global",
    "Attribute 4 default",
    "Attribute 6 default",
    "Attribute 1 default",
    "Attribute 2 default",
    "Attribute 8 name",
    "Attribute 8 value(s)",
    "Attribute 8 visible",
    "Attribute 8 global",
    "Attribute 5 default",
    "Attribute 7 default",
    "Attribute 8 default",
    "Attribute 9 name",
    "Attribute 9 value(s)",
    "Attribute 9 visible",
    "Attribute 9 global",
    "Attribute 9 default"

    """
    phrase = {
        'Material': 'Material',
        'Size': 'Size',
        'Color': 'Color',
        'Suitable': 'Suitable',
        'Brand': 'Brand',
        'Length': 'Length',
        'Finish': 'Finish',
        'Usage': 'Usage',
        'Material Used': 'Material',
        'Materials Used': 'Material',
        'Quantity': 'Quantity',
        'Available Color': 'Color',
        'Available Colors': 'Color',
        'Primary Material': 'Material',
        'Surface Finish': 'Surface Finish',
        'Trap Size': 'Trap Size',
        'Trap Distance': 'Trap Distance',
        'Colors': 'Color',
        'Bowl Dimensions': 'Bowl Dimension',
        'Single Bowl Dimensions': 'Single Bowl Dimension',
        'Left Bowl Dimensions': 'Left Bowl Dimension',
        'Right Bowl Dimensions': 'Right Bowl Dimension',
        'Trap Type': 'Trap Type',
        'Trap Types': 'Trap Type',
        'Dimension': 'Dimension',
        'Available Size': 'Size',
        'Application': 'Application',
        'Package Content': 'Package Content',
        'Installation Type': 'Installation Type',
        'Series': 'Series',
        'Capacity': 'Capacity',
        'Colour': 'Color',
        'Material Type': 'Material Type',
        'Item Form': 'Item Form',
        'Container Type': 'Container Type',
        'Room Type': 'Room Type',
        'Thichness': 'Thickness',
        'Warranty': 'Warranty',
        'Bowl Size': 'Bowl Size',
        'Left Bowl Size': 'Left Bowl Size',
        'Half Bowl Dimension': 'Half Bowl Dimension',
        'Half Bowl Dimensions': 'Half Bowl Dimensions',
        'Thickness': 'Thickness',
        'Thread Type': 'Thread Type',
        'Inlet Connection Size': 'Inlet Connection Size',
        'Suitable For': 'Suitable For',
        'Dimensions (mm)': 'Dimensions (mm)',
        'Key Feature': 'Key Feature',
        'Right Bowl Size': 'Right Bowl Size',
        'Brand Name': 'Brand Name',
        'Corner Radius': 'Corner Radius',
        'Package Contents': 'Package Contents',
        'Key Features': 'Key Features',
        'Salient Features': 'Salient Features',
        'Type': 'Type',
        'Country of Origin': 'Country of Origin',
        'Seating Height': 'Seating Height',
        'Shelf Life': 'Shelf Life',
        'Applications': 'Applications',
        'Weight': 'Weight',
        'Wieght': 'Weight',
        'Waste Coupling Type': 'Waste Coupling Type',
        'Other Features': 'Other Features',
        'Group': 'Group',
    }

    def add_arguments(self, parser):
        parser.add_argument('data_source_csv', type=str, help='please choose a path of images')
        parser.add_argument('--clear-db', action='store_true', help='do you want to clear current catalogue ?')

    parent = dict()
    parent_sku = dict()
    _cat = dict()

    def get_product(self, selector):
        if 'id:' in selector:
            return self.parent.get(selector.split('id:')[-1])
        elif selector in self.parent_sku:
            return self.parent_sku[selector]

    def set_product(self, product, line):
        self.parent[line['\ufeffID']] = product
        self.parent_sku[line['SKU']] = product

    def get_category(self, cat_line):
        cat_parent = None
        if not cat_line:
            return
        for cat in cat_line:
            if cat not in self._cat:
                if cat_parent is None:
                    method = Category.add_root
                    parent_slug = ''
                else:
                    method = cat_parent.add_child
                    parent_slug = cat_parent.slug + '--'
                self._cat[cat] = method(name=cat, slug=parent_slug + slugify(cat))
            cat_parent = self._cat[cat]
        return cat_parent

    pc = dict()
    attr_hash = dict()
    generic_pc = None

    def get_product_class(self, line):
        for i in range(1, 10):
            key = f'Attribute {i} name'
            if line.get(key, '').lower() == 'group':
                value_key = f'Attribute {i} value(s)'
                name = line.get(value_key)
                if not self.pc.get(name):
                    self.pc[name] = ProductClass.objects.get_or_create(name=name, defaults={'slug': slugify(name)})[0]
                print(key, '=', self.pc[name])
                return self.pc[name]
        if self.generic_pc is None:
            self.generic_pc = ProductClass.objects.get_or_create(name="Generic", slug="generic")[0]
        return self.generic_pc

    def get_attribute_field(self, name, field_type=ProductAttribute.TEXT, product_class_instance=None):
        if name not in self.attr_hash:
            self.attr_hash[name], _ = ProductAttribute.objects.get_or_create(
                product_class=product_class_instance,
                name=name,
                defaults={
                    'code': slugify(name, ).replace('-', '_'),
                    'type': field_type
                }
            )
        return self.attr_hash[name]

    def clear_data(self):
        print("Cleaning Earlier Dataset!")
        Product.objects.all().delete()
        Brand.objects.all().delete()
        Category.objects.all().delete()
        ProductClass.objects.all().delete()
        ProductImage.objects.all().delete()
        ProductAttributeValue.objects.all().delete()
        ProductAttribute.objects.all().delete()
        StockRecord.objects.all().delete()

    def clean_line(self, line):
        if '\ufeffName' in line:
            line['Name'] = line.pop('\ufeffName')
        return line

    def handle(self, *args, **kwargs):
        print(kwargs)
        if kwargs['clear_db']:
            self.clear_data()
        fields = [f'Attribute {i} name' for i in range(1, 9)]
        filename = kwargs['data_source_csv']
        struct = {
            'variable': Product.PARENT,
            'variation': Product.CHILD,
            'simple': Product.STANDALONE,
        }
        _cat = {}
        partner, _ = Partner.objects.get_or_create(name="ABC HAUZ")
        write = 3
        with open(filename, 'r') as _fp:
            contents = csv.DictReader(_fp)

            for line in contents:
                print("=" * 40)

                print("Getting Product Class...")
                product_class_instance = self.get_product_class(line)
                attrs, brand_name = self.get_attribute_dict(line, product_class_instance)
                print("Enrolling Brand...")
                brand = self.get_brand(brand_name)
                print(attrs)
                print(line)

                line = self.clean_line(line)

                print("Handling", line['Name'], "\n", " *** CATEGORIES *** ")
                cat_list = line['Categories'].split(' > ')
                cat_item = self.get_category(cat_list)
                parent_selector = line.get('Parent', '')
                _parent_obj = parent_selector and self.get_product(parent_selector)
                print(line['Regular price'] or 0, line['Sale price'] or 0, "===========")

                print("Saving Product Class...")
                try:
                    p = Product.objects.create(
                        product_class=product_class_instance,
                        structure=struct[line['Type']],
                        upc=line['SKU'] or str(uuid.uuid4()).split('-')[-1].upper(),
                        parent=_parent_obj or None,
                        title=line['Name'],
                        slug=slugify(line['Name']),
                        description=slugify(line['Description']),
                        about=slugify(line['Short description']),
                        weight=digit(line['Weight (kg)']),
                        length=digit(line.get('Length (mm)', line.get('Length (cm)', ))),
                        width=digit(line.get('Width (mm)', line.get('Width (cm)', ))),
                        height=digit(line.get('Height (mm)', line.get('Height (cm)', ))),
                        retail_price=digit(line['Regular price'] or 0),
                        effective_price=digit(line['Sale price'] or 0),
                        brand=brand,
                    )
                    print("Adding to Categories...")
                    p.categories.add(cat_item)
                except psycopg2.errors.UniqueViolation as e:
                    print(e)
                    continue
                except IntegrityError as e:
                    print(e)
                    continue
                print("Fetching Images...")
                for img in line['Images'].split(','):
                    pi = ProductImage(product=p)
                    fetch_image(img.strip(), pi, field='original', name=p.slug)

                print("Extracting Attributes...")
                # for f in line.keys():
                #     if f.startswith('Attribute') and f.endswith('name') and line.get(f):
                #         attr = self.get_attribute_field(line[f], self.get_suggested_field_type(f),
                #                                         product_class_instance=product_class_instance)
                #         
                for attr, attr_data in attrs.items():
                    setattr(p.attr, attr.code, attr_data['value'])
                    if attr.code == 'color':
                        pass
                p.save()
                if struct[line['Type']] == Product.PARENT:
                    print("Saving Parental details...")
                    self.set_product(p, line=line)
                else:
                    print("Updating Stock...")
                    StockRecord.objects.get_or_create(
                        partner=partner,
                        product=p,
                        cost_price=digit(line['Sale price']) or digit(line['Regular price']) / 1.18,
                        price_excl_tax=digit(line['Sale price']) / 1.18 or digit(line['Regular price']) / 1.18,
                        price_retail=digit(line['Regular price']),
                        num_in_stock=1000,
                        partner_sku=p.upc
                    )
        return

    def get_suggested_field_type(self, f):
        return ({
            'hexcolor': ProductAttribute.COLOR,
        }).get(slugify(f).replace('-', '_').lower(), ProductAttribute.TEXT)

    def get_attribute_dict(self, line, product_class_instance):
        fields = [
            (
                f'Attribute {i} name',
                f'Attribute {i} value(s)',
                f'Attribute {i} visible',
                f'Attribute {i} global',
                f'Attribute {i} default'
            ) for i in range(1, 9)]
        out = {}
        brand_name = None
        for same_attr_fields in fields:
            name, value, visibility, is_global, default = [line.get(f) for f in same_attr_fields]
            if not name:
                continue
            if name.lower() == 'brand':
                brand_name = value
                continue
            attr_field = self.get_attribute_field(
                name,
                field_type=self.get_suggested_field_type(name),
                product_class_instance=product_class_instance)
            out[attr_field] = {
                'value': value,
                'is_visible': visibility,
                'is_global': is_global,
                'default': default,
            }
            if attr_field.code == 'color':
                color_attr_field = self.get_attribute_field(
                    "HexColor",
                    field_type=self.get_suggested_field_type("HexColor"),
                    product_class_instance=product_class_instance)
                out[color_attr_field] = {
                    'value': '#FFFFFF',
                    'is_visible': False,
                    'is_global': is_global,
                }
        return out, brand_name

    def get_brand(self, brand_name):
        if brand_name is None:
            brand, _ = Brand.objects.get_or_create(name="Generic")
        else:
            brand, _ = Brand.objects.get_or_create(name=brand_name)
        return brand




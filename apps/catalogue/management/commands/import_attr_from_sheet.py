import functools
from collections import defaultdict
from pprint import pprint
from typing import Optional

from memoization import cached

from django.core.exceptions import ObjectDoesNotExist
from django.core.management import BaseCommand
import gspread
import pandas as pd
from django.utils.text import slugify
from oauth2client.service_account import ServiceAccountCredentials
from oscar.apps.catalogue.product_attributes import ProductAttributesContainer

from apps.catalogue.models import Product, Category, ProductAttribute, ProductClass, ProductAttributeValue, Brand
from oscar.apps.catalogue.categories import create_from_breadcrumbs

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('keys/fegnodevelopments-31659696681a.json', scope)

client = gspread.authorize(creds)
sheet = client.open('HAUZ DATA SHEET')  # 19
# sheet = sheet.worksheet('Cistern')


def memoize(func):
    out_map = {}

    def inner(*args, **kwargs):
        __key__ = ''
        for arg in args:
            __key__ += str(arg)
        for kwarg in kwargs:
            __key__ += kwarg + ':' + str(kwargs[kwarg])
        if __key__ not in out_map:
            out_map[__key__] = func(*args, **kwargs)
        return out_map[__key__]
    return inner


class AttributeUtils:

    def gsheet_dict_reader(self, sheet):
        # sheet = self.get_data_from_gsheet()
        num_cols = sheet.col_count
        num_rows = sheet.row_count

        dict_keys = []
        for key_index in range(1, num_cols + 1):
            dict_keys.append(sheet.cell(col=key_index, row=1).value)

        sheet_data = []
        for key_index in range(2, num_rows + 1):
            row = {}
            for key_index in range(1, num_cols + 1):
                index = dict_keys[key_index - 1]
                row[index] = sheet.cell(col=key_index, row=1).value
            yield row


class GetAttributes:

    ignorable_headers = ['id', 'name', 'structure', 'parent_id', 'category']
    analytics = defaultdict(lambda: defaultdict(lambda: 0))
    reporting = defaultdict(list)

    def compare_attributes(self, row, pc_title):
        p = self.find_product(row)
        if not p:
            print("product not found for row: ", row)
            self.analytics[pc_title]['product_not_found'] += 1
            self.reporting[pc_title].append(f"Product Not found : {row['name']}")

            return
        print(f"Product {p} : ")
        for attr in row:
            self.analytics[pc_title]['rows'] += 1
            if attr not in self.ignorable_headers:
                if row[attr]:
                    if not hasattr(p.attr, attr):
                        naming = " ".join([a[0].upper() + a[1:].lower() for a in attr.split('_')])
                        product_attr = ProductAttribute.objects.get_or_create(
                            product_class=p.get_product_class(),
                            code=attr,
                            defaults={'name': naming, "type": ProductAttribute.RICHTEXT},
                        )[0]
                        p.attr = ProductAttributesContainer(product=p)
                        pv = ProductAttributeValue(attribute=product_attr, product=p, )
                        pv.value = row[attr]
                        pv.save()
                        self.analytics[pc_title]['created_attributes'] += 1
                    if getattr(p.attr, attr) != row[attr]:
                        print(f"\tMismatch in attr values")
                        print(f"\t\t row['{attr}']: {row[attr]}")
                        print(f"\t\t p.attr.{attr}: {getattr(p.attr, attr)}")
                        self.analytics[pc_title]['attributes_mismatched'] += 1
                        self.reporting[pc_title].append(f"Trying to update: (Product-{p.id}).{attr} => From {getattr(p.attr, attr)} TO {row[attr]}")

                        # if (
                        #         getattr(p.attr, attr) == row[attr]
                        #         or str(getattr(p.attr, attr)).upper() == str(row[attr]).upper()
                        #         or (attr in ['brand', 'brand_name'] and getattr(p.attr, attr) == 'Generic')
                        #         or input("Wanna update database with new value ? ").upper() == "Y"
                        # ):

                        setattr(p.attr, attr, row[attr])
                        p.attr.save()
                        if attr in ['brand', 'brand_name']:
                            if p.brand.name != row[attr]:
                                p.brand.name = row[attr]
                                self.analytics[pc_title]['brands_updated'] += 1
                                p.brand.save()
                        self.analytics[pc_title]['attributes_updated'] += 1
                    else:
                        self.analytics[pc_title]['attributes_correct'] += 1

                else:
                    self.analytics[pc_title]['attributes_empty'] += 1
                    print(f"\trow['{attr}'] is empty")

        # if p.attr and hasattr(p.attr, 'brand'):
        #     p.attr.brand = p.brand.name
        # if p.attr and hasattr(p.attr, 'brand_name'):
        #     p.attr.brand_name = p.brand.name
        try:
            p.attr.save()
            self.analytics[pc_title]['attr_saved'] += 1
        except Exception as e:
            self.analytics[pc_title]['attr_exception'] += 1
            print(e)
            print("Error while saving attributes! Skipping ")
            input("")
        # print("Cleaning up \n\n")
        print("\n\n")

    def find_product(self, row):
        name = row['name']
        try:
            return Product.objects.select_related('brand').filter(title=name, structure__in=['standalone', 'child']).get()
        except Exception as e:
            if type(row['id']) is int:
                try:
                    return Product.objects.select_related('brand').get(pk=int(row['id']))
                except Exception as e:
                    print(e)
                    print(f"Product with title '{name}' or pk={row['id']} not found")
                    _idef = '#'
                    while _idef:
                        _idef = input("Do you have an id to share?")
                        if _idef and _idef.isdigit():
                            try:
                                return Product.objects.select_related('brand').get(pk=_idef)
                            except Exception as e:
                                print(e)


class SetAttributes:
    def set_product_from_row(self, row, product_class, utils, ignore_creation=False):
        _id = row['id']
        name = row['name']
        structure = row['structure']
        if structure == 'standalone':
            print("  [*]  ", name)
        if structure == 'parent':
            print("  [-]  ", name)
        if structure == 'child':
            print("   ----->  [*]  ", name)
        is_new_product = not _id or str(_id).startswith("#")
        if is_new_product:
            product: Product = self.get_product(row, product_class, utils)
        else:
            product: Product = Product.objects.get(id=_id)
            if not product.structure == structure:
                fn_name = f"move_{product.structure.lower()}_to_{structure.lower()}"
                fn = getattr(self, fn_name)
                product = fn(product, row, utils)
        if product.structure == Product.PARENT:
            utils['parent_hash'][_id] = product
        if product.structure == Product.CHILD:
            product.parent = utils['parent_hash'][row['parent_id']]
            product.save()
        if product.structure in [Product.CHILD, Product.STANDALONE]:
            self.set_attrs(product, row, utils=utils)

    def get_product(self, row, product_class, utils):
        _id = row['id']
        name = row['name']
        brand_name = row.get('brand')
        brand = self.get_brand(brand_name)
        structure = row['structure']
        parent_id = row['parent_id']

        product = Product(
            title=name,
            structure=structure,
            product_class=product_class,
            brand=brand,
            is_new_product=True,
        )

        if product.structure == Product.CHILD:
            product.parent = utils['parent_hash'][parent_id]
        product.save()

        if product.structure != product.CHILD:
            category = self.set_category(row, None)
            if category:
                product.categories.add(category)
        return product

    @cached
    def get_brand(self, brand_name):
        brand, _ = Brand.objects.get_or_create(name=brand_name)
        return brand

    ignorable_headers = ['id', 'name', 'structure', 'parent_id', 'category', 'id_old', 'parent_id_old']

    def set_attrs(self, p, row, utils=None):
        product = p
        for attr in row:
            if attr not in self.ignorable_headers and row[attr]:
                if not hasattr(p.attr, attr):
                    ProductAttribute.objects.create(
                        name=attr.replace('_', ' ').upper(), code=slugify(attr).replace('-', '_'),
                        product_class=p.get_product_class(),
                        is_new_product=True,
                    )
                    p.attr = ProductAttributesContainer(product=p)
            setattr(p.attr, attr, row[attr])
        p.save()

    def set_structure(self, p, row, utils=None):
        if not p:
            if utils is None:
                utils = {}
            if p.structure == p.CHILD:
                pass
            if p.structure == p.STANDALONE:
                if row['structure'] == p.PARENT:
                    self.move_standalone_to_parent(p, row, utils)
                elif row['structure'] == p.CHILD:
                    self.move_standalone_to_child(p, row, utils)

    def remove_stock(self, p):
        p.stockrecords.all().delete()

    def move_standalone_to_parent(self, p, row, utils):
        self.remove_stock(p)
        p.structure = p.PARENT
        p.attributesa.all().delete()
        utils['parent_hash'][row['id']] = p
        return p

    def move_standalone_to_child(self, p, row, utils):
        p.structure = p.CHILD
        p.product_class = None
        for c in p.categories.all():
            p.categories.remove(c)

        p.parent_id = utils['parent_hash'].get(row['parent_id'])
        return p

    def move_parent_to_child(self, p, row, utils):
        p.structure = p.CHILD
        p.parent_id = utils['parent_hash'].get(row['parent_id'])
        p.product_class = None
        for c in p.categories.all():
            p.categories.remove(c)
        return p

    def move_child_to_standalone(self, p: Product, row: dict, utils: dict):
        p.structure = p.STANDALONE
        for c in p.get_categories():
            p.categories.add(c)
        p.product_class = p.get_product_class()
        p.parent_id = None
        return p

    def move_child_to_parent(self, p: Product, row: dict, utils: dict):
        print(f"Trying to call move_child_to_parent({p}, {row}, <utils>) but failed!")
        return p

    def move_parent_to_standalone(self, p: Product, row: dict, utils: dict):
        print(f"Trying to call move_parent_to_standalone({p}, {row}, <utils>) but failed!")
        return p

    @cached
    def set_category(self, row, p, utils=None):
        if row['category']:
            return create_from_breadcrumbs(row['category'])


class Command(AttributeUtils, GetAttributes, SetAttributes, BaseCommand):

    pc_mapper = {
        "Copy of Kitchen Sink": "Kitchen Sink"
    }
    skippable_sheets = ['Kitchen Sink', 'categ', ]

    def extract_sheet(self, sheet):
        dataset = sheet.get_all_records()
        parent_products = {}
        pc_title = self.pc_mapper.get(sheet.title, sheet.title)
        pc, _ = ProductClass.objects.get_or_create(name=pc_title)

        for row in dataset:
            # self.set_product_from_row(row, product_class=pc, utils={'parent_hash': parent_products})
            # self.compare_attributes(row, pc_title)
            self.ensure_category(row, product_class=pc)

    def handle(self, *args, **options):
        workbook = client.open('HAUZ DATA SHEET')
        for i in range(0, 18):
            sheet = workbook.get_worksheet(i)     # copy of kitchen sink

            print("=======================================")
            if sheet.title in self.skippable_sheets:
                print("Skipping in ", sheet.title)
                continue
            print("Operating in ", sheet.title)
            # self.extract_sheet(sheet)
            if input("Do you want to proceed? ").lower() == "y":
                self.extract_sheet(sheet)
            else:
                print("Skipping.... ")
        print("=======================================")
        pprint(dict(self.analytics))
        pprint(dict(self.reporting))

    def ensure_category(self, row, product_class=None):
        if row['structure'] == 'child':
            # ignore category for child.
            return

        _id = row['id']
        product: Optional[Product] = None
        category = self.set_category(row, None)
        if _id and isinstance(_id, (int, )):
            product = Product.objects.filter(id=_id).first()
        if not product:
            product_set = Product.objects.filter(title__icontains=row['name'], structure=row['structure'])
            if len(product_set) <= 1:
                product: Product = product_set.first()
            else:
                print(f"Trying to process {product} with  {row.get('category')} ")
                max_count = 0
                max_count_pdt = None

                for p in product_set:
                    cnt = p.children.all().count()
                    if cnt > max_count:
                        max_count = cnt
                        max_count_pdt = p
                    elif cnt == max_count:
                        max_count = 0
                        max_count_pdt = None
                if max_count_pdt is None:
                    for attr in row:
                        if attr not in self.ignorable_headers and row[attr]:
                            print(attr, row[attr], '\t\t')

                    print(f"Currently running {row['id']}  => {row['name']} : {row['structure']}")
                    print("Please select the exacct product id from the list.")
                    for _p in product_set:
                        print(f"\t {_p.id}\t{_p.get_title()} ({_p.structure})  | Children = {_p.children.all().count()}")
                    print()
                    selection = input("Enter the ID OF Selected Product : ")
                    product = product_set.filter(pk=selection).first()
                    if product and input("Wanna delete all other products in this search " + str(product_set) + ' ?') == 'y':
                        product_set.exclude(pk=selection).delete()
                else:
                    product = max_count_pdt
        else:
            if product.categories.all().exists():
                return
        if category and category is not product.categories.all().first():
            product.categories.add(category)
            print(f"{product} is added to caegory: {category}!")
        print(" =============================================== ")









import functools
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

scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('keys/fegnodevelopments-31659696681a.json', scope)

client = gspread.authorize(creds)
sheet = client.open('HAUZ DATA SHEET')  # 19
# sheet = sheet.worksheet('Cistern')


def memoize(func):
    def inner(*args, **kwargs):
        return func(*args, **kwargs)
    return inner


class Command(BaseCommand):

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
    pc_mapper = {
        "Copy of Kitchen Sink": "Kitchen Sink"
    }
    skippable_sheets = ['Kitchen Sink', 'categ', 'Copy of Kitchen Sink']

    def extract_sheet(self, sheet):
        dataset = sheet.get_all_records()
        parent_products = {}
        pc_title = self.pc_mapper.get(sheet.title, sheet.title)

        pc, _ = ProductClass.objects.get_or_create(name=pc_title)

        for row in dataset:
            self.set_product_from_row(row, product_class=pc, utils={'parent_hash': parent_products})

    def handle(self, *args, **options):
        workbook = client.open('HAUZ DATA SHEET')
        for i in range(0, 18):
            sheet = workbook.get_worksheet(i)     # copy of kitchen sink
            print("=======================================")
            if sheet.title in self.skippable_sheets:
                print("Skipping in ", sheet.title)
                continue
            print("Operating in ", sheet.title)
            if input("Do you want to proceed? ").lower() == "y":
                self.extract_sheet(sheet)
            else:
                print("Skipping.... ")

    def set_product_from_row(self, row, product_class, utils):
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

    def set_attrs(self, p, row, utils=None):
        product = p
        ignorable_headers = ['id', 'name', 'structure', 'parent_id', 'category']
        for attr in row:
            if attr not in ignorable_headers and row[attr]:
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


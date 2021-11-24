from collections import defaultdict
from pprint import pprint

from cachetools import cached
from django.core.exceptions import ObjectDoesNotExist
from django.core.management import BaseCommand
import gspread
from django.template.defaultfilters import slugify
from oauth2client.service_account import ServiceAccountCredentials
from oscar.apps.catalogue.models import ProductCategory
from oscar.apps.catalogue.product_attributes import ProductAttributesContainer

from apps.catalogue.models import Product, Category, ProductAttribute, ProductClass, ProductAttributeValue, Brand
from oscar.apps.catalogue.categories import create_from_breadcrumbs

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('keys/fegnodevelopments-31659696681a.json', scope)

client = gspread.authorize(creds)
sheet = client.open('HAUZ DATA SHEET')  # 19


# sheet = sheet.worksheet('Cistern')

dbpids = Product.objects.all().values_list('pk', flat=True)


class RowHandler:
    ignorable_row_headers = ["id", "name", "structure", "parent_id", "category"]

    def __init__(self, row, pc, parent_products):
        self.row = row
        self.pc = pc
        self.parent_products = parent_products
        self._log()
        self.product = None
        self.product = self.get_from_saved()
        if self.product is None:
            print("Product Not Found! ", self.row['title'], self.row['id'])
            return
        # if self.is_product_saved():
        # else:
        #     self.product = self.create_from_row()
        if not self.product.is_child:
            self.set_category()
        else:
            self.set_attrs()

    def _log(self):
        structure = self.row['structure']
        name = self.row['name']

        if structure == 'standalone':
            print("  [*]  ", name)
        if structure == 'parent':
            print("  [-]  ", name)
        if structure == 'child':
            print("   ----->  [*]  ", name)

    def is_product_saved(self):
        _id = self.row['id']
        return _id and isinstance(_id, int) and _id in dbpids

    def get_brand(self, brand_name):
        if brand_name:
            brand, _ = Brand.objects.get_or_create(name=brand_name)
            return brand

    def set_category(self):
        if self.row['category'] and self.product.structure != Product.CHILD:
            category = create_from_breadcrumbs(self.row['category'])
            if category:
                print(self.row['category'], category, sep="\t")
                # ProductCategory.objects.all().filter(product=self.product).delete()
                self.product.categories.add(category)
                return category

    def get_from_saved(self):
        row = self.row
        _id = row['id']
        name = row['name']
        brand_name = row.get('brand') or row.get('brand_name')
        brand = self.get_brand(brand_name)
        structure = row['structure']
        parent_id = row['parent_id']

        name = row['name']
        if str(row['id']).isdigit():
            try:
                return Product.objects.select_related('brand').get(pk=int(row['id']))
            except Exception as e:
                print("Exception Caught, no product with this id.")
                try:
                    return Product.objects.select_related('brand').filter(title=name, structure__in=['standalone', 'child']).get()
                except Exception as e:
                    print(f"Product with title '{name}' or pk={row['id']} not found")
                    _idef = '#'
                    while _idef:
                        _idef = input("Do you have an id to share?")
                        if _idef and _idef.isdigit():
                            try:
                                return Product.objects.select_related('brand').get(pk=_idef)
                            except Exception as e:
                                print(e)
        print(f"Found row['id'] => {row['id']} ; trying to create new.")
        while input("Continue ? ") != "y":
            return self.create_from_row()

    def create_from_row(self):
        row = self.row
        _id = row['id']
        name = row['name']
        brand_name = row.get('brand') or row.get('brand_name')
        brand = self.get_brand(brand_name)
        structure = row['structure']
        parent_id = row['parent_id']

        product = Product(
            title=name,
            structure=structure,
            product_class=self.pc,
            brand=brand,
            is_new_product=True,
            search_tags=" ".join([name, self.pc.name] + [brand_name] if brand_name else [])
        )

        if product.structure == Product.CHILD:
            product.parent = self.parent_products[parent_id]
        product.save()
        print("New Product Created!")
        if product.structure == Product.PARENT:
            self.parent_products[_id] = product
        return product

    def set_attrs(self):
        product = self.product
        for attr in self.row:
            if attr not in self.ignorable_row_headers and self.row[attr]:
                if not hasattr(product.attr, attr):
                    attribute, _ = ProductAttribute.objects.get_or_create(
                        code=attr,
                        product_class=product.get_product_class(),
                        defaults={
                            "name": attr.replace('_', ' ').upper()
                        }
                    )
                    ProductAttributeValue.objects.create(product=product, attribute=attribute, value_text=self.row[attr])
                    product.attr.initialised = False
                else:
                    print(attr, self.row[attr], f"product.attr.{attr}", sep="\t")
                    if getattr(product.attr, attr) != self.row[attr]:
                        setattr(product.attr, attr, self.row[attr])
                        product.attr.save()

        product.save()

    def batch_update(self, sheet):
        sheet.batch_update([
            {"range": "A8:C8",
             "values": [["Texas", 5261485, 5261485]]},
            {"range": "A9:C9",
             "values": [["Wisconsin", 1630673, 1610065]]},
        ])


class Command(BaseCommand):
    pc_mapper = {
        # "Copy of Kitchen Sink": "Kitchen Sink"
    }
    skippable_sheets = ['Kitchen Sink', 'categ', ]

    def extract_sheet(self, sheet):
        dataset = sheet.get_all_records()
        parent_products = {}
        pc_title = self.pc_mapper.get(sheet.title, sheet.title)
        pc, _ = ProductClass.objects.get_or_create(name=pc_title)
        for row in dataset:
            rh = RowHandler(row, pc, parent_products)

    def handle(self, *args, **options):
        workbook = client.open('HAUZ DATA SHEET')
        for i in range(0, 18):
            sheet = workbook.get_worksheet(i)  # copy of kitchen sink
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

    analytics = defaultdict(lambda: defaultdict(lambda: 0))
    reporting = defaultdict(list)

from django.core.exceptions import ObjectDoesNotExist
from django.core.management import BaseCommand
import gspread
import pandas as pd
from django.utils.text import slugify
from oauth2client.service_account import ServiceAccountCredentials

from apps.catalogue.models import Product, Category, ProductAttribute, ProductClass
from oscar.apps.catalogue.categories import create_from_breadcrumbs

scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('keys/fegnodevelopments-31659696681a.json', scope)

client = gspread.authorize(creds)
sheet = client.open('HAUZ DATA SHEET')  # 19
# sheet = sheet.worksheet('Cistern')

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
    skippable_sheets = ['Kitchen Sink', 'categ']

    def extract_sheet(self, sheet):
        dataset = sheet.get_all_records()
        parent_products = {}
        if sheet.title in self.skippable_sheets:
            return
        pc_title = self.pc_mapper.get(sheet.title, sheet.title)

        pc, _ = ProductClass.objects.get_or_create(name=pc_title)

        for row in dataset:
            self.set_product_from_row(row, product_class=pc, utils={'parent_hash': {}})

    def handle(self, *args, **options):
        sheet = client.open('HAUZ DATA SHEET')
        sheet = sheet.get_worksheet(18)     # copy of kitchen sink
        self.extract_sheet(sheet)

    def set_product_from_row(self, row, product_class, utils):
        _id = row['id']
        name = row['name']
        structure = row['structure']
        parent_id = row['parent_id']
        category = row['category']

        is_new_product = not _id or str(_id).startswith('#')

        if is_new_product:
            p = Product(title=name, structure=structure, product_class=product_class)
        else:
            print("existing.......", _id, structure)
            # import pdb;pdb.set_trace()
            try:
                p = Product.objects.get(pk=_id)
            except ObjectDoesNotExist:
                if structure == 'child':
                    p = Product(title=name, structure=structure, product_class=None)
                    # import pdb;pdb.set_trace()
                else:
                    p = Product(title=name, structure=structure, product_class=product_class)
                    # import pdb;pdb.set_trace()


        self.set_structure(p, row, utils)

        if is_new_product:
            if structure in [p.STANDALONE, p.PARENT]:
                print(p,"$$$$$$$$$$$$$$$$$$$$$$$$$$$")
                p.product_class = product_class


        if structure != p.PARENT:
            self.set_attrs(p, row)
        if structure != p.CHILD:
            self.set_category(p, row, utils)
        p.save()
        # print(p.categories.all())

    def set_attrs(self, p, row):
        ignorable_headers = ['id', 'name', 'structure', 'parent_id', 'category']
        for attr in row:
            if attr not in ignorable_headers and row[attr]:
                if not hasattr(p.attr, attr):
                    ProductAttribute.objects.create(name=attr, code=slugify(attr).replace('-', '_'))
                # import pdb;pdb.set_trace()
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
                    self.get_standalone_to_parent(p, row, utils)
                elif row['structure'] == p.CHILD:
                    self.get_standalone_to_child(p, row, utils)

    def get_standalone_to_parent(self, p, row, utils):
        self.remove_stock(p)
        p.structure = p.PARENT
        utils['parent_hash'][row['id']] = p

    def remove_stock(self, p):
        p.stockrecords.all().delete()
        p.refresh_from_db()

    def get_standalone_to_child(self, p, row, utils):
        p.structure = p.CHILD
        p.parent_id = utils['parent_hash'].get(row['parent_id'])

    def set_category(self, p, row, utils):
        if row['category']:
            return create_from_breadcrumbs(row['category'])


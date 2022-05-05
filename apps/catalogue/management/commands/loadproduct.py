import os
from pprint import pprint
from urllib.request import urlopen

import gspread
import requests
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from django.core.management import BaseCommand
from collections import defaultdict

from django.utils.functional import lazy
from django.utils.text import slugify
from oauth2client.service_account import ServiceAccountCredentials
from oscar.apps.catalogue.categories import create_from_breadcrumbs
from apps.catalogue.models import ProductClass, ProductAttribute, Product, ProductImage, ProductAttributeValue, Category
from apps.partner.models import StockRecord, Partner
import pickle


class InMemoryDB:
    db = {}

    def __init__(self):
        self.cb_hell = []

    def store(self, pc, attrs):
        self.db[pc] = attrs

    def register_cb(self, fn):
        self.cb_hell.append(fn)

    def rollback(self):
        [fn() for fn in self.cb_hell]


memory = InMemoryDB()
abc_hauz = Partner.objects.get_or_create(name="ABC HAUZ")[0]


def prepare_product_class_data_from_datasheet(title, dataset):
    fields = [f'Attribute_{i}_name' for i in range(1, 10)]
    attrs = defaultdict(int)
    pc, pc_created = ProductClass.objects.get_or_create(name=title)
    for row in dataset:
        for field in fields:
            attrs[row[field]] += 1

    created_attrs = ProductAttribute.objects.bulk_create([
        ProductAttribute(
            name=attr,
            code=slugify(attr),
            type=ProductAttribute.TEXT,
            product_class=pc,
        ) for attr in attrs
    ])

    print(pc, created_attrs)

    @memory.register_cb
    def rollback():
        if pc_created:
            pc.delete()
        ProductAttribute.objects.filter(id__in=[at.id for at in created_attrs]).delete()
    return pc, created_attrs


def get_remote_images(product, url_list):
    i = 0
    for image_url in url_list.split(','):
        image_url = image_url.strip()
        ext = image_url.split('.')[-1]
        try:
            # generate temporary image
            img_temp = NamedTemporaryFile(delete=True)
            resp = requests.get(image_url)
            img_temp.write(resp.content)
            img_temp.flush()
            resp.close()

        except Exception as e:
            print('[x]  Could not fetch the image!' + str(e))
        else:
            # saving to model.
            product_img = ProductImage(caption=product.title, product=product, display_order=i)
            product_img.original.save(f"{slugify(product.title)}.{ext}", File(img_temp))
            product_img.save()
            i += 1


class CatalogueData(object):

    parent_product_queue = {}
    end_product_queue = []
    stock_queue = []

    def __init__(self, dataset, sheet_name, pc, attrs, catinfo):
        self.d = dataset
        self.class_name = sheet_name
        self.pc = pc
        self.attrs = attrs
        self.cat_info = catinfo

    def save(self, commit=False):
        d = self.d
        structure = {
            'variable': Product.PARENT, 'variation': Product.CHILD, 'simple': Product.STANDALONE
        }[d['Type'].lower().strip()]

        pdt = Product(
            wordpress_product_text=d['ID'],
            wordpress_product_id=d['WOO_ID'],
            structure=structure,
            upc=f"{d['SKU']}_{d['ID']}",
            parent=self.parent_product_queue[d['Parent']] if structure == Product.CHILD else None,
            title=d['Name'],
            seo_title=d['Name'],
            is_public=bool(d['Published']),
            slug=slugify(d['Name']),
            description=d['Description'],
            seo_description=d['Description'][:254],
            seo_keywords=d['Description'][:254],
            custom_search_tags=d['Tags'],
            product_class=self.pc,
            length=d['Length(mm)'] or 0,
            width=d['Width(mm)'] or 0,
            height=d['Height(mm)'] or 0,
            weight=d['Weight(kg)'] or 0,
            effective_price=d['Sale_price'] or 0,
            retail_price=d['Regular_price'] or 0,
            is_new_product=True,
        )
        s = structure == Product.STANDALONE
        p = structure == Product.PARENT
        c = structure == Product.CHILD
        pdt.save()
        print(d['SKU'])
        if p:
            self.parent_product_queue[d["ID"]] = pdt
        if c or s:
            self.end_product_queue.append(pdt)
            self.add_stock(pdt)

        if p or s:
            cats = self.cat_info.get(d['ID'], list())
            for cat in cats:
                pdt.categories.add(cat)

        if p or s or c:
            self.add_attributes(pdt)
        if d['Images']:
            get_remote_images(pdt, url_list=d['Images'])

    def add_attributes(self, pdt):
        fields = [(f'Attribute_{i}_name', f'Attribute_{i}_value(s)') for i in range(1, 10)]
        _attrs = {a.name: a for a in self.attrs}
        for name_field, val_field in fields:
            name = self.d[name_field]
            value = self.d[val_field]
            code = _attrs[name].code
            setattr(pdt.attr, code, value)
        pdt.attr.save()

    def add_stock(self, pdt):
        d = self.d
        StockRecord.objects.create(
            product=pdt,
            partner=abc_hauz,
            cost_price=d['Sale_price'] or 0,
            price_excl_tax=d['Sale_price'] or 0,
            price_retail=d['Regular_price'] or 0,
            partner_sku=d['SKU'],
            num_in_stock=100,
            low_stock_threshold=5,
        )


def get_workbook(sheet_id, specific_sheets=None):

    def get_workbook_authenticated():
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name('keys/fegnodevelopments-31659696681a.json', scope)
        client = gspread.authorize(creds)
        return client.open_by_key(sheet_id)

    base_filename = 'public/pickle/workbooks__{}.pkl'
    if specific_sheets:
        for sheet_title in specific_sheets:
            workbook = get_workbook_authenticated()
            sheet = workbook.worksheet(sheet_title)
            dataset = sheet.get_all_records()
            sheet_title = sheet.title
            yield sheet_title, dataset
    else:
        workbook = get_workbook_authenticated()
        for sheet in workbook.worksheets():
            yield sheet.title, sheet.get_all_records()


def cache_all_categories(pc, dataset):
    product_data_cat_map = {}
    for row in dataset:
        structure = row['Type'].lower().strip().replace('&amp;', '&')
        cats = [
            create_from_breadcrumbs(c)
            for c in row['Categories'].split(',')
        ]
        for c in cats:
            if c.product_class is None:
                c.product_class = pc
                c.save()
        if structure == "variation":
            key = row['Parent']
        elif structure == "simple":
            key = row['ID']
        else:
            continue
        product_data_cat_map[key] = cats
    return product_data_cat_map


class Command(BaseCommand):
    analytics = defaultdict(lambda: defaultdict(lambda: 0))
    reporting = defaultdict(list)
    readable_sheets = ["One Piece Toilet"]
    sheet_id = "19BFSfp95v1JxirCc03Hh6HWcLrCM7GCumVd9YezcXjE"  # ABC HAUZ Product Data OSCAR
    fields = (
        "ID", "WOO_ID", "Type", "SKU", "Name", "Published", "Is_featured", "Visibility_in_catalog",
        "Short_description", "Description", "Date_sale_price_starts", "Date_sale_price_ends", "Tax_status",
        "Tax_class", "In_stock", "Stock", "Low_stock_amount", "Sold_individually", "Weight(kg)", "Length(mm)",
        "Width(mm)", "Height(mm)", "Allow_customer_reviews", "Purchase_note", "Sale_price", "Regular_price",
        "Categories", "Tags", "Shipping_class", "Images", "Download_limit", "Download_expiry_days", "Parent",
        "Grouped_products", "Upsells", "Cross-sells", "External_URL", "Button_text", "Position",
        "Attribute_1_name", "Attribute_1_value(s)", "Attribute_1_visible", "Attribute_1_global",
        "Attribute_2_name", "Attribute_2_value(s)", "Attribute_2_visible", "Attribute_2_global",
        "Attribute_3_name", "Attribute_3_value(s)", "Attribute_3_visible", "Attribute_3_global",
        "Attribute_4_name", "Attribute_4_value(s)", "Attribute_4_visible", "Attribute_4_global",
        "Attribute_5_name", "Attribute_5_value(s)", "Attribute_5_visible", "Attribute_5_global",
        "Attribute_6_name", "Attribute_6_value(s)", "Attribute_6_visible", "Attribute_6_global",
        "Attribute_7_name", "Attribute_7_value(s)", "Attribute_7_visible", "Attribute_7_global",
        "Attribute_8_name", "Attribute_8_value(s)", "Attribute_8_visible", "Attribute_8_global",
        "Attribute_9_name", "Attribute_9_value(s)", "Attribute_9_visible", "Attribute_9_global",
        "Attribute_2_default", "Attribute_1_default", "Attribute_8_default"
    )

    def handle(self, *args, **options):
        self.clear_db()
        # workbook = get_workbook(self.sheet_id)
        workbook = get_workbook(self.sheet_id, specific_sheets=['Tile'])
        for sheet_title, dataset in workbook:
            pc, created_attrs = prepare_product_class_data_from_datasheet(sheet_title, dataset)
            self.extract_sheet(sheet_title, dataset, pc=pc, attrs=created_attrs)
            # memory.rollback()

    def extract_sheet(self, sheet_title, dataset, pc, attrs):
        catinfo = cache_all_categories(pc, dataset)
        for row in dataset:
            CatalogueData(row, sheet_name=sheet_title, pc=pc, attrs=attrs, catinfo=catinfo).save()

    def clear_db(self):
        Category.objects.all().delete()
        Product.objects.all().delete()
        ProductClass.objects.all().delete()
        ProductAttribute.objects.all().delete()
        ProductAttributeValue.objects.all().delete()
        ProductImage.objects.all().delete()
        StockRecord.objects.all().delete()







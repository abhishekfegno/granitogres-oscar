import os
import random

from django.conf import settings
from django.core.management import BaseCommand
from oscar.core.loading import get_model

from apps.catalogue.models import Product, Category, ProductClass, ProductAttribute, ProductImage, StockRecord
import csv
from faker import Faker
import uuid

fake = Faker()

import shutil
import os
from shutil import *

Partner = get_model('partner', 'Partner')


def copy_and_overwrite(from_path, to_path):
    if os.path.exists(to_path):
        shutil.rmtree(to_path)
    shutil.copytree(from_path, to_path)


def copytree(src, dst, symlinks=False, ignore=None):
    names = os.listdir(src)
    if ignore is not None:
        ignored_names = ignore(src, names)
    else:
        ignored_names = set()

    if not os.path.isdir(dst):      # This one line does the trick
        os.makedirs(dst)
    errors = []
    for name in names:
        if name in ignored_names:
            continue
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)
        try:
            if symlinks and os.path.islink(srcname):
                linkto = os.readlink(srcname)
                os.symlink(linkto, dstname)
            elif os.path.isdir(srcname):
                copytree(srcname, dstname, symlinks, ignore)
            else:
                # Will raise a SpecialFileError for unsupported file types
                copy2(srcname, dstname)
        # catch the Error from the recursive copytree so that we can
        # continue with other files
        except Error as err:
            errors.extend(err.args[0])
        except EnvironmentError as why:
            errors.append((srcname, dstname, str(why)))
        print('.', end='', )
    try:
        copystat(src, dst)
    except OSError as why:
            errors.extend((src, dst, str(why)))
    if errors:
        raise Exception(errors)


weight_labels = [
    (
        {'label': '500 g',  'multiplier': 0.5},
        {'label': '1 kg',  'multiplier': 1},
        {'label': '2 kg',  'multiplier': 2},
        {'label': '5 kg',  'multiplier': 5}
    ), (
        {'label': '125 g',  'multiplier': 0.125},
        {'label': '250 kg',  'multiplier': 0.25},
        {'label': '500 kg',  'multiplier': 0.5},
        {'label': '1 kg',  'multiplier': 1}
    ), (
        {'label': '1 kg',  'multiplier': 1},
        {'label': '2 kg',  'multiplier': 2},
        {'label': '3 kg',  'multiplier': 3},
        {'label': '4 kg',  'multiplier': 4}
    ), (
        {'label': '500 g',  'multiplier': 0.5},
        {'label': '1 kg',  'multiplier': 1},
        {'label': '1.5 kg',  'multiplier': 1.5},
        {'label': '2 kg',  'multiplier': 2}
    )
]


class DISPLAY:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class Command(BaseCommand):
    """
    python manage.py generate_products ../
    """

    file_path = os.path.join(settings.BASE_DIR, 'public/')
    csv_name = 'grocery_products.csv'
    media_folder = 'public/media/'
    product_upload_folder = 'products/scripted/'
    source_folder = None
    img_list = []

    def add_arguments(self, parser):
        parser.add_argument('data_source_folder', type=str, help='please choose a path of images')
        parser.add_argument('--copy',  help=f'Copy These Folders to "{self.media_folder}{self.product_upload_folder}"')

    def get_asset_url(self, path, file_path=True):
        path = "/".join(path.split('/')[2:])
        return f'{self.media_folder if file_path else ""}{self.product_upload_folder}{path}'

    def handle(self, *args, **options):
        self.file_path = options['data_source_folder']
        _copy = options.get('copy')

        Product.objects.all().delete()
        Category.objects.all().delete()
        ProductImage.objects.all().delete()
        # then restore missing files from source file.
        if _copy:
            _copy_true_path = (os.path.join if _copy.startswith('/') else lambda _, x: x)(settings.BASE_DIR, _copy)
            _dest_true_path = os.path.join(settings.BASE_DIR, self.media_folder, self.product_upload_folder)
            print(f"Copying From \n\tSource: {_copy_true_path} \n\t Destination: {_dest_true_path}")
            copytree(_copy_true_path, _dest_true_path)
            print()

        lines = []
        csv_file = self.file_path
        partner = Partner.objects.all().first()
        if not partner:
            partner = Partner.objects.create(name="Central Shop")
        FMCG, _created = ProductClass.objects.get_or_create(name="FMCG")

        class M:
            name = 0
            name_id = 1
            category = 2
            cat_id = 3
            image_path = 4
            description_file = 5

        pa_weight, _ = ProductAttribute.objects.get_or_create(product_class=FMCG, name='Weight', code='weight',
                                                              is_varying=True, type=ProductAttribute.TEXT)
        with open(csv_file, newline='') as csvfile:
            lines = csv.reader(csvfile, delimiter=',', quotechar='"')
            for row in lines:
                # skip header row
                if '(str)' in row[M.name]: continue # since lines is not an iterator.

                ## INITIALIZNG VARIABLES
                # Initialize a random weight set for varients.
                weight_label = random.choice(weight_labels)

                # listing categories
                cat_obj = None
                name_set = row[M.image_path].split('/')
                cat_list = name_set[2: -2]
                if len(cat_list) == 1:
                    cat_list.append("Others")
                cat_obj_list = Category.get_root_nodes()
                print(cat_list)
                img_path = self.get_asset_url(
                    row[M.image_path]
                )
                print(f"{img_path}")
                if not os.path.isfile(os.path.join(settings.BASE_DIR, img_path)):
                    print(f"Accessing : {img_path} ::: FAILED!!! ")
                    raise Exception(f"File Not found: {os.path.join(settings.BASE_DIR, img_path)}")
                img_url = self.get_asset_url(
                    row[M.image_path], file_path=False
                )
                # Getting Category Object from cat name.
                k = 1
                for cat in cat_list:
                    new_cat_obj = cat_obj_list.filter(name=cat).first()
                    if new_cat_obj is None:
                        if not cat_obj:
                            new_cat_obj = Category.add_root(name=cat)
                        else:
                            new_cat_obj = cat_obj.add_child(name=cat)   # noqa
                        new_cat_obj.image = img_url
                        new_cat_obj.save()
                        print("Created Category: ", "  " * new_cat_obj.depth,
                              DISPLAY.WARNING + "=> {}".format(new_cat_obj) + DISPLAY.ENDC)
                    cat_obj = new_cat_obj
                    cat_obj_list = new_cat_obj.get_children()
                    print("  cat: ", "  " * 4 * k, repr(cat_obj))

                # Log
                parent_product_title = '{} {}'.format(
                    row[M.name],
                    row[M.category] if row[M.category] != row[M.name] else '',
                )
                print(f"Generating Product: {DISPLAY.HEADER}\"{parent_product_title}\"{DISPLAY.ENDC}", end='')
                print(f"\t{DISPLAY.OKGREEN}...OK{DISPLAY.ENDC}", )
                short_description = ""
                with open(
                        os.path.join(
                            settings.BASE_DIR,
                            self.get_asset_url(row[M.description_file])
                        ), 'r') as description_file:
                    short_description = description_file.read()
                parent_product = Product.objects.create(
                    structure=Product.PARENT,
                    title=parent_product_title,
                    is_public=True,
                    upc=None,
                    description=short_description,
                    product_class=FMCG,
                )
                parent_product.categories.add(cat_obj)
                price = random.randrange(1000, 29050) / 100
                print(f"\tPRICE: {price}")
                parent_product.images.create(
                    original=img_url,
                    caption=parent_product_title,
                )
                print(f"\tIMAGE: {img_path}")

                for i in range(4):
                    product_title = '{} {}'.format(
                        parent_product_title,
                        weight_label[i]["label"]
                    )
                    print(f"\tGenerating Child Product: {DISPLAY.HEADER}\"{product_title}\"{DISPLAY.ENDC}", end="")

                    child_product = Product.objects.create(
                        structure=Product.CHILD,
                        title=product_title,
                        is_public=True,
                        upc=None,
                        description=short_description,
                        product_class=FMCG,
                        parent=parent_product
                    )
                    child_product.categories.add(cat_obj)
                    sr = StockRecord.objects.filter(partner=partner, product=child_product).first()
                    if not sr:
                        sr = StockRecord.objects.create(
                            partner=partner,
                            product=child_product,
                            partner_sku=uuid.uuid4().hex[:6].upper(),
                            price_currency="INR",
                            price_excl_tax=price * weight_label[i]['multiplier'],
                            price_retail=price * random.randrange(12, 28) / 10,
                            cost_price=price * random.randrange(4, 8) / 10,
                            num_in_stock=random.randrange(100, 1000),
                        )
                    child_product.images.create(
                        original=img_url,
                        caption=product_title,
                    )
                    print(f"\t\t...{DISPLAY.OKGREEN}OK{DISPLAY.ENDC}", )
                    print(f"\t\tPRICE: {sr.price_excl_tax}")
                    print(f"\t\tWEIGH: { weight_label[i]['multiplier']}")

                    pa_weight.save_value(child_product, weight_label[i]['label'])




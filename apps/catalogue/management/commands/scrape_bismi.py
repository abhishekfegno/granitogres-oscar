import json
import logging
import os
import random
import re
import sys
import uuid as uuid
from typing import Optional
from urllib.request import urlopen

import requests
from django.conf import settings
from django.core.cache import cache
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from django.core.management import BaseCommand
from django.utils.text import slugify
from oscar.core.loading import get_model

from apps.catalogue.management.routers.bismi import BismiStore
from apps.catalogue.models import Product, Category, ProductClass, ProductAttribute, ProductImage, StockRecord

Partner = get_model('partner', 'Partner')


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    python manage.py generate_bbt_products fruits-vegetables
    """
    fmcg = None
    partner = None
    pa_weight = None
    category_slug = None
    category_name = None
    img_list = []
    categories = [
    ]
    weight = re.compile('([0-9.]+)')

    def set_categories(self):
        self.categories = BismiStore().fetch_categories()['listFeaturedCategory']

    @staticmethod
    def clear_current_catalogue():
        if input("Clear Catalogue ? [Y/n]").lower() == 'y':
            print(' *** Clearing Current Catalogue! ***')
            Category.objects.all().delete()
            Product.objects.all().delete()
            ProductImage.objects.all().delete()
            ProductImage.objects.all().delete()
        if input("Clear Order History ? [Y/n]").lower() == 'y':
            from apps.order.management.commands.clearorders import Command as ClearOrderCommand
            ClearOrderCommand().handle()

    @staticmethod
    def get_a_partner():
        partner = Partner.objects.all().first()
        if not partner:
            partner = Partner.objects.create(name="Central Shop")
        return partner

    @staticmethod
    def get_product_class():
        return ProductClass.objects.get_or_create(name="FMCG")[0]

    @staticmethod
    def get_remote_image(product, image):
        logger.info('[ ]  Fetching images from url : ' + image)
        try:
            ext = image.split('.')[-1]
            img_temp = NamedTemporaryFile(delete=True)
            img_temp.write(urlopen(image).read())
            img_temp.flush()
            product_img = ProductImage(caption=product.title, product=product)
            product_img.original.save(f"{slugify(product.title)}.{ext}", File(img_temp))
            product_img.save()
        except Exception as e:
            logger.error('[x]  Could not fetch the image!' + str(e))

    @staticmethod
    def get_remote_image_for_category(category, image):
        try:
            ext = image.split('.')[-1]
            img_temp = NamedTemporaryFile(delete=True)
            img_temp.write(urlopen(image).read())
            img_temp.flush()

            category.image.save(f"{slugify(category.name)}.{ext}", File(img_temp))
            category.icon.save(f"{slugify(category.name)}_icon.{ext}", File(img_temp))
            category.save()
        except Exception as e:
            logger.error('[x]  Could not fetch the image!' + str(e))

    def generate_stock_record(self, product, mrp, retail_price, ):
        sr = StockRecord.objects.filter(partner=self.partner, product=product).first()
        if not sr:
            logger.info('[ ]  Generating Stock!')
            sr = StockRecord.objects.create(
                partner=self.partner,
                product=product,
                partner_sku=uuid.uuid4().hex.upper(),
                price_currency="INR",
                price_excl_tax=retail_price/1.18,       # reducing GST of 18%
                price_retail=mrp,
                num_in_stock=2500,
            )
        return sr

    def create_product(self, data):

        has_weight_label = data['Title'][-2:] in ['KG', 'ML', '0G', 'GM', 'LT'] and data['Title'][-2:]
        if has_weight_label == '0G':
            has_weight_label = 'G'
        numbers = self.weight.findall(data['Title'])
        weight = float(numbers[-1]) if len(numbers) else 1

        is_standalone = has_weight_label is False
        print("[ ] Fetching " + data['Title'], " AS ", "STANDALONE " if is_standalone else "PARENT")
        title_split = data['Title'].split(' ')
        pdt_title = " ".join(title_split[:-1]) + (title_split[-1] if is_standalone else '')
        main_product = Product.objects.create(
            structure=Product.STANDALONE if is_standalone else Product.PARENT,
            title=pdt_title,
            is_public=True,
            upc=uuid.uuid4().hex[:9].upper(),
            description=data['Description'],
            product_class=self.fmcg
        )

        if is_standalone:
            self.pa_weight.save_value(product=main_product, value=(weight or 1))
            self.generate_stock_record(main_product, data['Mrp'], data['FinalPrice'])
        else:
            self._create_fake_child(main_product, weight=weight, has_weight_label=has_weight_label, **data)
        self.get_remote_image(main_product, image=data['ProductImage'])
        return main_product

    def _create_fake_child(self, parent, **dataset):
        for i in (1, 2, 4):
            weight_label = str(i * dataset['weight']) + ' ' + dataset['has_weight_label']
            child_title = parent.title + " - " + weight_label
            print("[ ]               GENERATING " + child_title)
            product = Product.objects.create(
                structure=Product.CHILD,
                title=child_title,
                is_public=True,
                upc=uuid.uuid4().hex[:9].upper(),
                parent=parent,
                description=child_title,
            )
            self.pa_weight.save_value(product=product, value=weight_label)
            self.generate_stock_record(product, i * dataset['Mrp'], i * dataset['FinalPrice'])     # redusing gst
            if dataset['ProductImage']:
                self.get_remote_image(product, image=dataset['ProductImage'])

    # def _create_child(self, parent, child_dataset):
    #     for data in child_dataset:
    #         print('             [ ] Creating Child! ', data['pc_n'], data['w'])
    #         product = Product.objects.create(
    #             structure=Product.CHILD,
    #             title=data['pc_n'] + " - " + data.get('w', ''),
    #             is_public=True,
    #             upc=uuid.uuid4().hex[:9].upper(),
    #             parent=parent,
    #             description=data['p_desc'],
    #         )
    #         self.pa_weight.save_value(product=product, value=data['w'])
    #         self.generate_stock_record(product, data['mrp'], data['sp'])
    #         self.get_remote_image(product, image=data['p_img_url'])

    def get_category_object(self, cat_name, img=None, parent=None):
        cat_name_slug = slugify(cat_name)

        if parent is None:
            main_cat: Optional[Category] = Category.get_root_nodes().filter(name=cat_name_slug).first()
            if main_cat is None:
                main_cat: Category = Category.add_root(slug=cat_name_slug, name=cat_name)

        else:
            main_cat = parent.get_descendants().filter(name=cat_name_slug).first()
            if main_cat is None:
                main_cat: Category = parent.add_child(slug=cat_name_slug, name=cat_name)

        if img:
            self.get_remote_image_for_category(main_cat, img)

        return main_cat

    @staticmethod
    def generate_data(categoey, sub_category, sub_cat_dict_data):
        category_slug = f'{categoey.slug}-{sub_category.slug}'

        def generator(**kwargs):
            data = BismiStore().fetch_product(**kwargs)['listProduct']
            for product in data:
                yield product

        return generator(
            slug=category_slug,
            category_id=sub_cat_dict_data['CategoryID'],
            group_id=sub_cat_dict_data['GroupID']
        )

    def initialize(self):
        self.set_categories()
        self.clear_current_catalogue()
        self.partner: Partner = self.get_a_partner()
        self.fmcg: ProductClass = self.get_product_class()
        self.pa_weight, _ = ProductAttribute.objects.get_or_create(
            product_class=self.fmcg, name='Weight', code='weight',
            is_varying=True, type=ProductAttribute.TEXT)

    def handle(self, *args, **options):
        self.initialize()

        for cat in self.categories:

            main_cat: Category = self.get_category_object(cat['CategoryTitle'], cat['CategoryImagePath'])

            for sub_cat in cat['listGroup']:
                sub_category: Category = self.get_category_object(sub_cat['GroupTitle'], sub_cat['GroupImagePath'], parent=main_cat)

                data_set = self.generate_data(main_cat, sub_category, sub_cat)
                [_ for _ in data_set]
                print(1)
                # for row in data_set:
                #     product = self.create_product(row)
                #     product.categories.add(sub_category)

        cache.clear()

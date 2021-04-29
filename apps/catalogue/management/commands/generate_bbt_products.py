import logging
import random
import uuid as uuid
from urllib.request import urlopen

import requests
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from django.core.management import BaseCommand
from django.utils.text import slugify
from oscar.core.loading import get_model

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
        {"category": "Fruits & Vegetables", "sub-category": "Cuts & Sprouts", 'slug': "/fruits-vegetables/cuts-sprouts/"},
        {"category": "Fruits & Vegetables", "sub-category": "Exotic Fruits & Veggies", 'slug': "/fruits-vegetables/exotic-fruits-veggies/"},
        {"category": "Fruits & Vegetables", "sub-category": "Fresh Fruits", 'slug': "/fruits-vegetables/fresh-fruits/"},
        {"category": "Fruits & Vegetables", "sub-category": "Fresh Vegetables", 'slug': "/fruits-vegetables/fresh-vegetables/"},
        {"category": "Fruits & Vegetables", "sub-category": "Herbs & Seasonings", 'slug': "/fruits-vegetables/herbs-seasonings/"},
        {"category": "Fruits & Vegetables", "sub-category": "Organic Fruits & Vegetables", 'slug': "/fruits-vegetables/organic-fruits-vegetables/"},

        {"category": "Eggs, Meat & Fish", "sub-category": "Eggs", 'slug': "/eggs-meat-fish/eggs/"},
        {"category": "Eggs, Meat & Fish", "sub-category": "Fish & Sea Food", 'slug': "/eggs-meat-fish/fish-seafood/"},
        {"category": "Eggs, Meat & Fish", "sub-category": "Mutton & Lamb", 'slug': "/eggs-meat-fish/mutton-lamb/"},
        {"category": "Eggs, Meat & Fish", "sub-category": "Pork & Other Meats", 'slug': "/eggs-meat-fish/pork-other-meats/"},
        {"category": "Eggs, Meat & Fish", "sub-category": "Poultry", 'slug': "/eggs-meat-fish/poultry/"},

        {"category": "Beverages", "sub-category": "Coffee", 'slug': "/beverages/coffee/"},
        {"category": "Beverages", "sub-category": "Energy & Soft Drinks", 'slug': "/beverages/energy-soft-drinks/"},
        {"category": "Beverages", "sub-category": "Fruit Juices & Drinks", 'slug': "/beverages/fruit-juices-drinks/"},
        {"category": "Beverages", "sub-category": "Health Drink & Supplement", 'slug': "/beverages/health-drink-supplement/"},
        {"category": "Beverages", "sub-category": "Tea", 'slug': "/beverages/tea/"},
        {"category": "Beverages", "sub-category": "Water", 'slug': "/beverages/water/"},
    ]

    @staticmethod
    def generate_data(category_slug):
        url = "https://www.bigbasket.com/product/get-products/?slug={category_slug}&page=1&tab_type=[" \
              "%22all%22]&sorted_on=popularity&listtype=pc"

        def generator(_category_slug):
            response = requests.get(url.format(category_slug=_category_slug))
            response_json = response.json()
            data = response_json['tab_info'][0]['product_info']['products']
            for product in data:
                print(' => Yielding Next Product!')
                yield product

            # _page_no = 1
            # up_to_page_no = None
            # while up_to_page_no is None or up_to_page_no <= _page_no:
            #     response = requests.get(url.format(category_slug=_category_slug, page_no=_page_no))
            #     response_json = response.json()
            #     _page_no += 1
            #     if (_page_no-1) == 1:
            #         response_json = response.json()
            #         data = response_json['tab_info'][0]['product_info']['products']
            #         if up_to_page_no is None:
            #             up_to_page_no = response_json['tab_info'][0]['product_info']['tot_pages']
            #     else:
            #         data = response_json['tab_info']['product_map']['all']['prods']
            #     for product in data:
            #         yield product

        return generator(category_slug)

    @staticmethod
    def clear_current_catalogue():
        if input("Clear Catalogue ? [Y/n]").lower() is not 'n':
            print(' *** Clearing Current Catalogue! ***')
            Product.objects.all().delete()
            Category.objects.all().delete()
            ProductImage.objects.all().delete()

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

    def generate_stock_record(self, product, mrp, retail_price, ):
        sr = StockRecord.objects.filter(partner=self.partner, product=product).first()
        if not sr:
            logger.info('[ ]  Generating Stock!')
            sr = StockRecord.objects.create(
                partner=self.partner,
                product=product,
                partner_sku=uuid.uuid4().hex[:6].upper(),
                price_currency="INR",
                price_excl_tax=mrp,
                price_retail=retail_price,
                num_in_stock=random.randrange(100, 600),
            )
        return sr

    def create_product(self, data):
        print("[ ] Fetching " + data['pc_n'])
        is_standalone = len(data['all_prods']) == 0
        main_product = Product.objects.create(
            structure=Product.STANDALONE if is_standalone else Product.PARENT,
            title=data['pc_n'],
            is_public=True,
            upc=uuid.uuid4().hex[:9].upper(),
            description=data['p_desc'],
            product_class=self.fmcg
        )

        if is_standalone:
            self.pa_weight.save_value(product=main_product, value=data['w'])
            self.generate_stock_record(main_product, data['mrp'], data['sp'])
        else:
            self._create_child(parent=main_product, child_dataset=data['all_prods'])
        self.get_remote_image(main_product, image=data['p_img_url'])
        return main_product

    def _create_child(self, parent, child_dataset):
        for data in child_dataset:
            print('             [ ] Creating Child! ', data['pc_n'], data['w'])
            product = Product.objects.create(
                structure=Product.CHILD,
                title=data['pc_n'] + " - " + data.get('w', ''),
                is_public=True,
                upc=uuid.uuid4().hex[:9].upper(),
                parent=parent,
                description=data['p_desc'],
            )
            self.pa_weight.save_value(product=product, value=data['w'])
            self.generate_stock_record(product, data['mrp'], data['sp'])
            self.get_remote_image(product, image=data['p_img_url'])

    def handle(self, *args, **options):
        self.partner: Partner = self.get_a_partner()
        self.fmcg: ProductClass = self.get_product_class()
        self.pa_weight, _ = ProductAttribute.objects.get_or_create(
            product_class=self.fmcg, name='Weight', code='weight',
            is_varying=True, type=ProductAttribute.TEXT)

        for cat in self.categories:
            cat_name = cat['category']
            sub_cat_name = cat['sub-category']
            slug = cat['slug']
            cat_name_slug, sub_cat_slug = slug.strip('/').split('/')
            print(cat_name, sub_cat_name)
            main_cat: Category = (
                    Category.objects.filter(slug=cat_name_slug).first()
                    or Category.add_root(slug=cat_name_slug, name=cat_name)
            )
            sub_cat: Category = (
                    main_cat.get_descendants().filter(slug=sub_cat_slug).first()
                    or main_cat.add_child(slug=sub_cat_slug, name=sub_cat_name)
            )
            data_set = self.generate_data(slug)
            for row in data_set:
                product = self.create_product(row)
                product.categories.add(sub_cat)

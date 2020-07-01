import os
import random

from django.conf import settings
from django.core.management import BaseCommand
from oscar.core.loading import get_model

from apps.catalogue.models import Product, Category, ProductClass, ProductAttribute, ProductImage
import csv
from faker import Faker
import uuid

fake = Faker()
Partner = get_model('partner', 'Partner')
StockRecord = get_model('partner', 'StockRecord')


class Command(BaseCommand):

    file_path = '~/woodncart-dataset/'
    csv_name = 'dataset.csv'
    product_upload_folder = 'public/media/images/products/up/'
    img_list = []

    def add_arguments(self, parser):
        parser.add_argument('path', type=str, help='please choose a path of dataset')

    def load_img_list(self):
        _path = os.path.join(settings.BASE_DIR, self.product_upload_folder)
        self.img_list = [name for name in os.listdir(_path)
                         if os.path.isfile(os.path.join(_path, name)) and name.endswith('.jpg')]

    def handle(self, *args, **kwargs):
        self.file_path = kwargs['path']
        self.load_img_list()
        lines = []
        csv_file = os.path.join(self.file_path, self.csv_name)
        partners = Partner.objects.all()

        class M:
            sl_no = 0
            item_id = 1
            name = 2
            category = 3
            price = 4
            old_price = 5
            sellable_online = 6
            link = 7
            other_colors = 8
            short_description = 9
            designer = 10
            depth = 11
            height = 12
            width = 13
            weight = 14

        with open(csv_file, newline='') as csvfile:
            lines = csv.reader(csvfile, delimiter=',', quotechar='"')
            for row in lines:
                if row[M.item_id] == 'item_id':  # skip header row
                    continue
                print(f"Adding Product :{row[M.sl_no]} ->  {row[M.item_id]}.......")

                p_class = ProductClass.objects.filter(name__iexact=row[M.category]).first()
                if not p_class:
                    p_class = ProductClass(name=row[M.category], )
                    p_class.save()
                default = {'product_class': p_class, 'type': ProductAttribute.FLOAT}
                pa_depth, _ = ProductAttribute.objects.get_or_create(name='Depth', code='depth', **default)
                pa_height, _ = ProductAttribute.objects.get_or_create(name='Height', code='height', **default)
                pa_width, _ = ProductAttribute.objects.get_or_create(name='Width', code='width', **default)
                pa_weight, _ = ProductAttribute.objects.get_or_create(name='Weight', code='weight', **default)

                cat = Category.objects.filter(name__iexact=row[M.category]).first()
                if not cat:
                    cat = Category.add_root(name=row[M.category])
                    cat.save()
                product = Product.objects.create(
                    structure=Product.STANDALONE,
                    title=f'{row[M.name]} {row[M.category]} {row[M.item_id]}',
                    is_public=True,
                    upc=None,
                    description=row[M.short_description],
                    product_class=p_class,
                    effective_price=(float(row[M.price]) or 0) * 1.18,
                    retail_price=(float(row[M.old_price].strip('SR ').replace(',', '').replace('/4 pack', '').replace('/2 pack', '')) if row[M.old_price].startswith('SR ') else 0) * 1.18,
                    additional_product_information=fake.text(),
                    care_instructions=fake.paragraph(),
                    merchant_details=fake.paragraph(),
                    customer_redressal=fake.paragraph(),
                    returns_and_cancellations=fake.paragraph(),
                    warranty_and_installation=fake.paragraph(),
                )
                product.categories.add(cat)
                if row[M.depth]:
                    pa_depth.save_value(product, row[M.depth])
                if row[M.height]:
                    pa_height.save_value(product, row[M.height])
                if row[M.width]:
                    pa_width.save_value(product, row[M.width])
                if row[M.weight]:
                    pa_weight.save_value(product, row[M.weight])

                for partner in partners:
                    price = float(row[M.price]) or 0

                    sr = StockRecord.objects.filter(partner=partner, product=product).first()
                    if not sr:
                        StockRecord.objects.create(
                            partner=partner,
                            product=product,
                            partner_sku=uuid.uuid4().hex[:6].upper(),
                            price_currency="INR",
                            price_excl_tax=price,
                            price_retail=price * random.randrange(12, 48) / 10,
                            cost_price=price * random.randrange(4, 8) / 10,
                            num_in_stock=random.randrange(50, 1000),
                        )
                for i in range(0, random.randrange(2, 8)):
                    product.images.create(
                        original=f'{self.product_upload_folder}{random.choice(self.img_list)}'
                    )





import requests
from django.core.management import BaseCommand
from rest_framework.reverse import reverse

from apps.api_set_v2.tests.test_homepage_api import UserCreds
from apps.catalogue.documents import Product
from apps.mod_oscarapi.serializers.product import Range


class Command(BaseCommand):

    def setUp(self):
        self.test_user = UserCreds().user
        self.url = 'https://abchauz.dev.fegno.com' + reverse('api-index-v2')
        req = requests.get(self.url)
        self.index_api_response = req.json()
        print(self.index_api_response)

    def get_content_from_slug(self, slug):
        for content in self.index_api_response['content']:
            if content['slug'] == slug:
                return content

    def _test_common_range(self, slug, title, ):
        products__range, _created = Range.objects.using('default').get_or_create(
            slug=slug, defaults={'name': title, 'is_public': True, })
        content = self.get_content_from_slug(slug)

        if content is None:
            print(f'Cannot find {slug} in Api ({self.url})!')
        if content['content'] is not []:
            print(f'Cannot find {slug} in Api ({self.url})!')

        p_ids = [pdt['id'] for pdt in content['content']]
        pdts = Product.objects.using('default').filter(pk__in=p_ids)
        if not pdts.exists():
            print(f"No products found in {title}")
        for excl_prod in pdts:
            if not products__range.contains_product(excl_prod):
                print(f"Product {excl_prod} is not in {slug} Range.")
        print("Test for ", title, "Completed!")

    def test_index_api__exclusive_products(self):
        self._test_common_range('exclusive-products', 'Exclusive Products')

    def test_index_api__furniture_products(self):
        self._test_common_range('furnitures-for-your-home', 'Furnitures for your home')

    def test_index_api__picked_products(self):
        self._test_common_range('picked-for-you', 'Picked for you')

    def test_index_api__customer_favorites(self):
        self._test_common_range('customer-favorites', 'Customer Favorites')

    def handle(self, *args, **options):
        self.setUp()
        self.test_index_api__customer_favorites()
        self.test_index_api__picked_products()
        self.test_index_api__furniture_products()
        self.test_index_api__exclusive_products()



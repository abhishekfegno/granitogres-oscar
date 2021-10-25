from django.test import TestCase
from oscar.apps.offer.models import Range
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from apps.catalogue.models import Product
from apps.users.models import User


class UserCreds:
    username = "testing"
    password = "password!@#"

    def __init__(self):
        try:
            self.user = User.objects.create_user(username=self.username, password=self.password)
        except Exception as e:
            self.user = User.objects.get(username=self.username)


class IndexApiTestCase(TestCase):

    def setUp(self):
        self.test_user = UserCreds().user
        self.client = APIClient()
        self.client.login(username=self.test_user.username, password=self.test_user.password)
        self.url = reverse('api-index-v2')
        self.index_api_response = self.client.get(self.url, format='json').json()

    def get_content_from_slug(self, slug):
        for content in self.index_api_response['content']:
            if content['slug'] == slug:
                return content

    def _test_common_range(self, slug, title, ):
        products__range, _created = Range.objects.using('default').get_or_create(
            slug=slug, defaults={'name': title, 'is_public': True, })
        content = self.get_content_from_slug(slug)
        self.assertIsNotNone(content, f'Cannot find {slug} in Api ({self.url})!')
        self.assertIsNot(content['content'], [], f'There are no products in {slug}!')
        p_ids = [pdt['id'] for pdt in content['content']]
        pdts = Product.objects.using('default').filter(pk__in=p_ids)
        self.assertTrue(pdts.exists(), f"No products found in {title}")
        for excl_prod in pdts:
            self.assertTrue(products__range.contains_product(excl_prod), f"Product {excl_prod} is not in {slug} Range.")
        print("Test for ", title, "Completed!")

    def test_index_api__exclusive_products(self):
        self._test_common_range('exclusive-products', 'Exclusive Products')

    def test_index_api__furniture_products(self):
        self._test_common_range('furnitures-for-your-home', 'Furnitures for your home')

    def test_index_api__picked_products(self):
        self._test_common_range('picked-for-you', 'Picked for you')

    def test_index_api__customer_favorites(self):
        self._test_common_range('customer-favorites', 'Customer Favorites')



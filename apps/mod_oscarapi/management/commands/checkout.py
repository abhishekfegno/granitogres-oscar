import json
import sys
from random import randint

import requests
from django.conf import settings
from django.core.management import BaseCommand
from django.urls import reverse
from django.utils.module_loading import import_string
from oscar.core.loading import get_model
from oscarapicheckout import utils
from oscarapicheckout.serializers import OrderSerializer
from oscarapicheckout.signals import order_placed
from oscarapicheckout.states import DECLINED, CONSUMED

from apps.availability.models import Zones
from apps.basket.models import Basket
from apps.catalogue.models import Product
from apps.dashboard.custom.models import empty
from apps.mod_oscarapi.serializers.checkout import CheckoutSerializer
from apps.partner.strategy import Selector
from apps.users.models import User

get_methods = []
for method in settings.API_ENABLED_PAYMENT_METHODS:
    get_methods.append(import_string(method['method'])())


class Command(BaseCommand):
    user = None
    s = None            # store request with session
    _passwd = None
    serializer_class = CheckoutSerializer
    BASE_URL = 'http://{}/api/v1/'

    def add_arguments(self, parser):
        parser.add_argument(
            '--method', help=f'Get Payment Mode, Must be one of {[met.code for met in get_methods]}', default='cash'
        )
        parser.add_argument(
            '--password',  default='asdf1234', help="Enter password, if password is not 'asdf1234' (Dev Settings)"
        )
        parser.add_argument(
            '--host',  default='localhost:8000', help="Enter Host Name."
        )
        parser.add_argument(
            '--num-orders',  default='1', help="Number of orders you want to generate."
        )
        parser.add_argument(
            '--print-users',  action='store_true', help="Print Users List"
        )
        # parser.add_argument(
        #     '--random-user',  action='store_true', help="Print Users List"
        # )
        parser.add_argument(
            '--user',  default='1', help='Get User',
        )

    def post(self, _method):
        basket = self.populate_basket(no_of_products_needed=randint(2, 6))
        data = self.generate_data(
                basket, basket.owner, _method
        )
        self.checkout(data)

    def get_user(self, **options):
        self.user = User.objects.filter(pk=options['user']).first()

    def handle(self, *args, **options):
        _method = None
        self.BASE_URL = self.BASE_URL.format(options['host'])
        if options['print_users']:
            self.user = User.objects.order_by('?').first()
            print("Username\t| ID\t| First Name\t| is_active")
            for user in User.objects.all():
                print(f" {user.username}\t| {user.id}\t| {user.get_short_name()}\t| {user.is_active}")
            return

        self.get_user(**options)
        if not self.user:
            return

        self._passwd = options['password']

        if options['method'] not in [met.code for met in get_methods]:
            print(f"Invalid Input Types. Must be one of {[met.code for met in get_methods]}")
            return
        for met in get_methods:
            if met.code == options['method']:
                _method = met
                break
        self.login(self.user)

        for i in range(int(options['num_orders'])):
            print(f"Generating Cart #{i+1}......!")
            self.post(_method)

    def login(self, user):
        s = requests.Session()
        login_data = {"username": user.username, "email": user.email,  "password": self._passwd}
        response = s.post(
            self.BASE_URL + 'rest-auth/login/',
            login_data
        )
        print("Logged in Status ", response)
        if response.status_code == 200:
            print("Logged in as : ", user.get_short_name(), "[ ", user.pk, " ]")
            self.s = s
            return
        print("Could Not Login")
        print(response.text)
        sys.exit(0)

    def checkout(self, data):
        response = self.s.post(
            self.BASE_URL + 'checkout/',
            json=data,
            headers={'Content-Type': 'application/json'}
        )
        # print("DATA : ")
        # print(json.dumps(data))
        print(response)
        # if 200 <= response.status_code < 410:
        #     print(response.text)

    def populate_basket(self, no_of_products_needed=3):

        qs = Product.objects.filter(
                structure__in=[Product.STANDALONE, Product.CHILD]
        ).values_list('id', flat=True).order_by('?')[:no_of_products_needed]

        for product in qs:
            post_url = self.BASE_URL + 'basket/add-product/'
            product_url = self.BASE_URL + 'products/' + str(product) + '/'
            qty = randint(2, 10)
            self.s.post(
                post_url,
                {
                    'url': product_url,
                    'quantity': qty
                }
            )
            print(f"Added {qty} items of  {product}")
        basket = Basket.open.get(owner_id=self.user.id)
        basket.strategy = Selector().strategy(user=basket.owner)
        basket.save()
        return basket

    def generate_data(self, basket, user=None, method=None):
        # if method == 'cash':
        #     payment =
        # elif method == 'razor_pay':
        #     payment = {
        #         method: {
        #             "enabled": True,
        #             "pay_balance": True
        #         }
        #     }
        #     raise NotImplemented()
        # else:
        #     raise ModuleNotFoundError()

        return {
            "basket": f"https://store.demo.fegno.com/api/v1/baskets/{basket.id}/",
            "guest_email": "",
            "total": float(basket.total_incl_tax),
            "shipping_method_code": "free_shipping",
            "shipping_charge": {
                "excl_tax": 0.0,
                "currency": "INR",
                "incl_tax": 0.0,
                "tax": 0.0
            },
            "shipping_address":{
                "title": "Mr",
                "first_name": "JERIN",
                "last_name": "JOHN",
                "line1": "Kachirackal House",
                "line2": "Vennikulam P O",
                "line3": "Thiruvalla",
                "line4": "Thiruvalla",
                "state": "Kerala",
                "postcode": "689544",
                "phone_number": "+919446600863",
                "notes": "",
                "country": "https://store.demo.fegno.com/api/v1/countries/IN/"
            },
            "billing_address": {
                "title": "Mr",
                "first_name": "JERIN",
                "last_name": "JOHN",
                "line1": "Kachirackal House",
                "line2": "Vennikulam P O",
                "line3": "Thiruvalla",
                "line4": "Thiruvalla",
                "state": "Kerala",
                "postcode": "689544",
                "phone_number": "+919446600863",
                "notes": "",
                "country": "https://store.demo.fegno.com/api/v1/countries/IN/"
            },
            "payment": {
                "cash": {
                    "enabled": True,
                    "amount": float(basket.total_incl_tax)
                },
                "razor_pay": {
                    "enabled": False
                }
            }
        }


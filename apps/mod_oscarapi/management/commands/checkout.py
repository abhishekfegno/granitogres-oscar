import json
import sys
from random import randint

import requests
from django.conf import settings
from django.contrib.gis.geos import Point
from django.core.management import BaseCommand
from django.utils.module_loading import import_string
from apps.address.models import UserAddress, Country

from apps.basket.models import Basket
from apps.catalogue.models import Product
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
    BASE_URL = '{}://{}/api/v1/'

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
            '--checkout-current',  action='store_true', help="No need to add any products, just checkout as it is."
        )
        parser.add_argument(
            '--num-orders',  default='1', help="Number of orders you want to generate."
        )
        parser.add_argument(
            '--secure',  default=False, help="needs https request?."
        )
        parser.add_argument(
            '--print-users',  action='store_true', help="Print Users List"
        )
        parser.add_argument(
            '--user',  default='1', help='Get User id',
        )

    def post(self, _method, checkout_only_current_basket=False):
        if checkout_only_current_basket:
            basket = self.populate_basket(no_of_products_needed=0)
        else:
            basket = self.populate_basket(no_of_products_needed=randint(1, 2))
        data = self.generate_data(
            basket, basket.owner, _method
        )
        print(json.dumps(data))
        self.checkout(data)

    def get_user(self, **options):
        self.user = User.objects.filter(pk=options['user']).first()

    def handle(self, *args, **options):
        _method = None
        self.options = options
        self.BASE_URL = self.BASE_URL.format('https' if options['secure'] else 'http', options['host'])
        print(self.BASE_URL)
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
            print(f"Generating Cart #{ i + 1 }......!")
            self.post(_method, options['checkout_current'] and options['num_orders'] == '1')

        # to_returned =
        # to_return_approval =
        # to_return_request =
        # to_delivered =
        # to_out_for_delivery = options['confirm_order']
        # to_confirm_order = options['confirm_order'] or to_out_for_delivery

    def login(self, user):
        s = requests.Session()
        login_data = {"username": user.username, "email": user.email,  "password": self._passwd}
        response = s.post(
            self.BASE_URL + 'rest-auth/login/',
            login_data
        )
        print("REQUEST: ", login_data)
        print("Logged in Status ", response)
        if response.status_code == 200:
            print("Logged in as : ", user.get_short_name(), "[", user.username, "]")
            self.s = s
            if response.headers.get('X-Geo-Location-ID') == 'None':
                self.s.get(self.BASE_URL)
            return
        else:
            print("Could Not Login")
            print("RESPONSE: ", response.text)
            if input("Exit? Y/n") in 'Yy':
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
        if 200 < response.status_code or response.status_code > 204:
            print(response.text)

    def populate_basket(self, no_of_products_needed=3):

        qs = Product.objects.filter(
            structure__in=[Product.STANDALONE, Product.CHILD]
        ).values_list('id', flat=True).order_by('?')[:no_of_products_needed]

        for product in qs:
            post_url = self.BASE_URL + 'basket/add-product/'
            product_url = self.BASE_URL + 'products/' + str(product) + '/'
            qty = randint(1, 2)
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
        basket_url = self.BASE_URL + '_basket/'
        if method.code == 'cash':
            payment = {"payment": "cash"}
        elif method.code == 'razor_pay':
            response = self.s.get(basket_url).json()
            total_rate = response['net_total']['incl_tax']
            print(f"Open {self.BASE_URL.replace('/api/v1/', '/rzp/')}?amt={int(total_rate * 100)} ")
            print(f'Amount : INR {total_rate} /-')
            rzp_key = input("razorpay_payment_id : ")
            print(rzp_key)
            # rzp_key = input(f"razorpay payment id for amount '{int(basket.total_incl_tax * 100)}' : ")
            payment = {
                "payment": "razor_pay",
                "razorpay_payment_id": rzp_key
            }
        else:
            print(basket, user, method)
            raise ModuleNotFoundError("Method is not in ")
        uad = UserAddress.objects.filter().last()
        point = Point(float(12.785238498732), float(77.94478155806023))
        if uad is None:
            uad = UserAddress.objects.create(
                user=user,
                **{
                    "title": "Mr",
                    "first_name": "JERIN",
                    "last_name": "JOHN",
                    "line1": "Kachirackal House",
                    "line2": "Vennikulam P O",
                    "line3": "Thiruvalla",
                    "line4": "Thiruvalla",
                    "line5": "Thiruvalla",
                    "state": "Kerala",
                    "postcode": "689544",
                    "location": point,
                    # "phone_number": "+919446600863",
                    # "notes": "",
                    "country": Country.objects.get(pk='IN')
                }
                # is_default_for_shipping=True,
                # is_default_for_billing=True,
            )
        if uad.location is None:
            uad.location = point
            uad.save()
        req_body = {
            "basket": f"https://store.demo.fegno.com/api/v1/baskets/{basket.id}/",
            "basket_id": basket.id,
            "notes": "Some Notes for address as string.",
            "phone_number": "+919497270863",
            "shipping_address": uad.id,
            "billing_address": uad.id,
            **payment
        }
        print(req_body)
        return req_body

    def generate_data_old(self, basket, user=None, method=None):
        if method.code == 'cash':
            payment = {
                "cash": {
                    "enabled": True,
                    "amount": float(basket.total_incl_tax)
                },
                "razor_pay": {
                    "enabled": False
                }
            }
        elif method.code == 'razor_pay':
            print(f"Open {self.BASE_URL.replace('/api/v1/', '/rzp/')}?amt={int(basket.total_incl_tax * 100)} ")
            print(f'Amount : INR {basket.total_incl_tax} /-')
            rzp_key = input("razorpay_payment_id : ")
            print(rzp_key)
            # rzp_key = input(f"razorpay payment id for amount '{int(basket.total_incl_tax * 100)}' : ")
            payment = {
                "cash": {
                    "enabled": False,
                },
                "razor_pay": {
                    "enabled": True,
                    "amount": float(basket.total_incl_tax),
                    "razorpay_payment_id": rzp_key
                }
            }
        else:
            print(basket, user, method)
            raise ModuleNotFoundError("Method is not in ")

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
            "shipping_address": {
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
            "payment": payment
        }




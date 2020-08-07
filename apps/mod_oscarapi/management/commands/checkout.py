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

    def add_arguments(self, parser):
        parser.add_argument(
            '--method', help=f'Get Payment Mode, Must be one of {[met.code for met in get_methods]}', default='cash'
        )
        parser.add_argument(
            'user_id', help='Get User',
        )

    def handle(self, *args, **kwargs):
        try:
            user = User.objects.get(pk=kwargs['user_id'])
        except Exception as e:
            return print(e)

        if kwargs['method'] not in [met.code for met in get_methods]:
            print(f"Invalid Input Types. Must be one of {[met.code for met in get_methods]}")
            return
        method = None
        for met in get_methods:
            if met.code == kwargs['method']:
                method = met
                break
        self.post(kwargs['user_id'], method)

        print("Cart Ordered Successfully!")

    def generate_data(self, basket, user, method):
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
            "billing_address":{
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
                    # "pay_balance": True
                    "amount": float(basket.total_incl_tax)
                },
                "razor_pay": {
                    "enabled": False
                }
            }
        }


    serializer_class = CheckoutSerializer

    def post(self, user_id, method):
        import json
        s = requests.Session()
        login_data = {"username": "9497270863", "email": "admin@fegno.com",  "password": "asdf1234"}
        BASE_URL = 'http://localhost:8000/api/v1/'
        response = s.post(
            BASE_URL + 'rest-auth/login/',
            login_data
        )
        for product in Product.objects.filter(
                structure__in=[Product.STANDALONE, Product.CHILD]
        ).values_list('id', flat=True)[:randint(2, 6)]:
            post_url = BASE_URL + 'basket/add-product/'
            product_url = BASE_URL + 'products/' + str(product) + '/'
            s.post(
                post_url,
                {
                    'url': product_url,
                    'quantity': randint(2, 10)
                }
            )
        basket = Basket.open.get(owner_id=user_id)
        basket.strategy = Selector().strategy(user=basket.owner)
        basket.save()
        data = self.generate_data(
                basket, basket.owner, method
            )
        response = s.post(
            BASE_URL + 'checkout/',
            json=data,
            headers={'Content-Type': 'application/json'}
        )
        print("DATA : ")
        print(json.dumps(data))
        print(response)
        if 200 <= response.status_code < 410:
            print(response.text)


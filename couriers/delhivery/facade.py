import json
from pprint import pprint
from random import randint
from typing import Any, Optional, Union, Sequence, Iterable

import requests
from requests import Response
from rest_framework import status

from apps.order.models import Order
from couriers.delhivery import settings as app_settings

"""
Error: ClientWarehouse matching query does not exist.
    the 'CLIENT' name you are using is not added to database by Delhivery, contact them back!

"""


# compatible with django-oscar!
# class Country:
#     name = None
#
# class PhoneNumber:
#     national_number = None

# class ShippingAddress():
#     first_name = None
#     last_name = None
#     address = None
#     city = None
#     state = None
#     country = Country()
#     address_type = 'home/office'
#     summary = None
#     phone_number = PhoneNumber()

#
# class Order:
#     number = 'order-number'
#     shipping_address = ShippingAddress()


class BadRequest(Exception):
    message = "Bad Request"


class Delhivery(object):

    def __init__(self):
        if app_settings.IN_PRODUCTION:
            self.BASE_URL = app_settings.PRODUCTION_URL
            self.TOKEN = app_settings.PRODUCTION_TOKEN
            self.CLIENT = app_settings.CLIENT
            self.WAREHOUSE = app_settings.PRODUCTION_PICKUP_WAREHOUSE
        else:
            self.BASE_URL = app_settings.STAGING_URL
            self.TOKEN = app_settings.STAGING_TOKEN
            self.CLIENT = app_settings.STAGING_CLIENT
            self.WAREHOUSE = app_settings.STAGING_PICKUP_WAREHOUSE

        self.headers = {
            'Authorization': f'Token {self.TOKEN}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

    def dict_to_uri(self, params: dict) -> str:
        params['token'] = self.TOKEN
        return '?' + ('&'.join([f"{k}={v}" for k, v in params.items()]))

    def pincode_servicibility(self, pincode: str) -> Optional[dict]:
        if not pincode:
            raise BadRequest("No Pincode Delivered")
        uri: str = f'{self.BASE_URL}/c/api/pin-codes/json/'
        params: dict = {
            'filter_codes': pincode,
            # 'covid_zone': 'R|O|G',    # Covid Zone filter
            # 'dt': "YYYY-MM-DD",       # on or after date
            # 'st': 'KL',               # state filter
        }
        uri += self.dict_to_uri(params)
        try:
            r: Response = requests.get(uri, )
            if r.status_code == 200:
                """
                r.json() => {"delivery_codes":[{
                    "postal_code": {
                        "covid_zone":"R", "pin":456010, "max_amount":0,
                        "pre_paid":"Y", "cash":"Y", "pickup":"Y", "repl":"Y", "cod":"Y", "country_code":"IN", 
                        "sort_code":"UJJ/SAK", "is_oda":"N", "district":"Ujjain", "state_code":"MP", "max_weight":0
                    }
                }]}
                """
                dc: list = r.json()['delivery_codes']
                if dc:
                    return dc[0]["postal_code"]
            raise BadRequest(r.text)
        except Exception as e:
            print(e)
            return None

    def generate_bulk_waybill(self, count=1) -> Optional[list]:
        uri: str = f'{self.BASE_URL}/waybill/api/bulk/json/'
        params: dict = {
            'cl': app_settings.CLIENT,
            'count': count,
        }
        uri += self.dict_to_uri(params)

        try:
            r: Response = requests.get(uri)
            if r.status_code == 200:
                response_text:str = r.text
                return response_text.strip('"').split(',')
            raise BadRequest(r.text)
        except Exception as e:
            print(e)
            return None

    def pre_generate_waybill(self) -> Optional[str]:
        uri = f'{self.BASE_URL}/waybill/api/fetch/json/'
        params = {'cl': app_settings.CLIENT}
        uri += self.dict_to_uri(params)

        try:
            r = requests.get(uri)
            if r.status_code == 200:
                response_text: str = r.text
                return response_text.strip('"')
            raise BadRequest(r.text)
        except Exception as e:
            print(e)
            return

    def customer_warehouse_generation(self, shipping_address) -> Iterable[Union[Optional[dict], Optional[str]]]:
        uri = f"{self.BASE_URL}/api/backend/clientwarehouse/create/"
        params = {
            # random unique slug
            "name": app_settings.SHIPPING_ADDRESS_UNIQUE_SLUG.format(id=shipping_address.id) + f"{randint(1,99999999999999999)}",   # (mandatory)
            "registered_name": shipping_address.salutation,
            "address": shipping_address.summary,
            "add": shipping_address.summary,                                                    # (mandatory)
            "address_type": shipping_address.address_type,     # home/office                    # (optional)
            "city": shipping_address.city,
            "state": shipping_address.state,
            "country": shipping_address.country.name,
            "pin": shipping_address.postcode,                                                   # (mandatory)
            "phone": shipping_address.phone_number.national_number,                             # (mandatory)

            "return_name": app_settings.PICKUP_LOCATION['name'],
            "return_add": app_settings.PICKUP,                                                  # (optional)
            "return_address": app_settings.PICKUP,                                              # (optional)
            "return_city": app_settings.PICKUP_LOCATION['city'],
            "return_state": app_settings.PICKUP_LOCATION['state'],
            "return_country": app_settings.PICKUP_LOCATION['country'],
            "return_pin": app_settings.PIN_CODE,
            "return_phone": app_settings.MOBILE,
        }
        try:
            r = requests.post(uri, data=json.dumps(params), headers=self.headers)
            if r.status_code == status.HTTP_200_OK:
                return r.json(), params['name']
            elif r.status_code == status.HTTP_201_CREATED:
                return r.json(), params['name']
            return r.json(), None
        except Exception as e:
            print("P4")
            print(e)
            return None, None

    def pack_order(self, order: Order, reverse=False) -> Union[dict, str, None]:
        uri = f'{self.BASE_URL}/api/cmu/create.json'
        if not order.waybill:
            order.waybill = self.pre_generate_waybill()
            order.save()

        response, customer_warehouse = self.customer_warehouse_generation(order.shipping_address)
        if response is None:
            print("Warehouse Generation Failed!", type(response))
            return
        if response['error']:
            print(response['error'][0])
            return None
        if response.get('data', {}).get('name'):
            customer_warehouse = response.get('data', {}).get('name')
        pprint(customer_warehouse)
        pprint(response)

        data = {
            "pickup_location": app_settings.PICKUP_LOCATION,
            "shipments": [{
                'product_quantity': order.num_items,
                "waybill": order.waybill,
                "client": self.CLIENT,
                "name": customer_warehouse,
                "order": order.number,
                "order_date": order.date_placed.strftime("%Y-%m-%d %H:%M:%S"),  # (optional)
                "product_desc": f"{order.shipping_address.notes or ''}\n\nThis box contains {order.shipping_description}",
                "payment_mode": order.payment_type_for_delhivery() if not reverse else 'Pickup',
                "total_amount": float(order.total_incl_tax),
                # "name": order.shipping_address.salutation,  # (mandatory)
                "add": order.shipping_address.summary,  # (mandatory)
                "address_type": order.shipping_address.address_type,  # (optional)        # home/office
                "city": order.shipping_address.city,
                "state": order.shipping_address.state,
                "country": order.shipping_address.country.name,
                "pin": order.shipping_address.postcode,  # (mandatory)
                "phone": f"{order.shipping_address.phone_number.national_number}",  # (mandatory)
                'consignee_gst_tin': app_settings.SELLER_GSTIN,
                'seller_gst_tin': app_settings.SELLER_GSTIN,
                'seller_name': app_settings.CLIENT_NAME,
                'seller_add': app_settings.PICKUP,
                "extra_parameters": None,                             # (optional)
            }],
        }
        params = {'format': 'json', 'data': json.dumps(data), }
        try:
            print("==== FOR POSTMAN ====")
            print("format=json&data=" + json.dumps(data))
            print("==== FOR POSTMAN END ====")

            r = requests.post(uri, data=params, headers=self.headers)
            if r.status_code == 200:
                return r.json()
            raise BadRequest(r.text)
        except Exception as e:
            print(e)
            return None

    def pack_return(self, order: Order) -> Optional[str]:
        print("Return Package Called ")
        return self.pack_order(order, reverse=True)

    def cancel_courier(self, order):
        """
        https://staging-express.delhivery.com/api/p/edit
        """
        uri = f'{self.BASE_URL}/api/p/edit'
        try:
            r = requests.post(uri, json={
                "waybill": order.waybill,
                "cancellation": "true"
            }, headers=self.headers)
            if r.status_code == status.HTTP_200_OK:
                return r.text
            raise BadRequest(r.text)
        except Exception as e:
            print(e)
            return None

    def get_packing_slip(self, order):
        """
            DEPRICATED
        """
        return

    def track_order(self, waybill):
        """
        https://track.delhivery.com/api/v1/packages/json/?waybill=4866610000534&token=07.......45d7e0541a16
        """
        uri = f"{self.BASE_URL}/api/v1/packages/json/?waybill={waybill}&token={self.TOKEN}"
        resp = requests.get(uri)
        return resp.json(), resp.status_code

    def request_pickup(self, date, time, pickup_obj=None):
        """
        https://staging-express.delhivery.com/fm/request/new/
        Authorization : Token xxxxxxxxxxxxxxxxxxxx
        Content-Type : application/json
        {
            "pickup_time": "18:30:00",
            "pickup_date": "2017-08-29",
            "pickup_location": "xxxxxxxxxxxxxxxxx",
            "expected_package_count": 1
        }

        """
        uri = f"{self.BASE_URL}/fm/request/new/"
        try:
            resp = requests.post(uri, json={
                "pickup_time": time.strftime("%H:%M:%S"),
                "pickup_date": date.strftime("%Y-%m-%d"),
                "pickup_location": self.CLIENT,
                "expected_package_count": 1
            }, headers=self.headers)
            if resp.status_code == status.HTTP_201_CREATED:
                if pickup_obj:
                    pickup_obj.response = resp.json()
                return resp.json()
            raise BadRequest(resp.json())
        except Exception as e:
            print("Exception", e)
            return None










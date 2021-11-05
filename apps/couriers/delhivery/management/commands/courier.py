import datetime

from django.core.management import BaseCommand
from couriers.delhivery.facade import Delhivery as D
import requests
from rest_framework import status
from apps.order.models import Order
from couriers.delhivery import settings as app_settings


class BadRequest(Exception):
    message = "Bad Request"


class Command(BaseCommand):

    def handle(self, *args, **options):
        d = D()

        oo = Order.objects.order_by('?').last()
        # check pincode serviceability
        # oo.shipping_address.postcode = '682026'
        # oo.shipping_address.save()
        # print(d.pincode_servicibility('689544'))

        # print(d.client_warehouse_generation(oo.shipping_address))
        print(d.pack_order(oo))
        print(d.pack_return(oo))

        # ########### Pickup request!
        # now = datetime.datetime.now()
        # date = now.date() + datetime.timedelta(days=2)
        # time = datetime.time(hour=10, minute=2)
        # print(d.request_pickup(date, time))



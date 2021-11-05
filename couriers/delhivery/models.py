import json

from django.conf import settings
from django.db import models
from django.utils.functional import cached_property
from jsonfield import JSONField
from oscar.apps.order import exceptions

from apps.order.models import Order
from couriers.delhivery.facade import Delhivery


class RequestPickUp(models.Model):
    response = JSONField(default=None, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    date = models.DateField(null=True)
    time = models.TimeField(null=True)
    completed = models.BooleanField(null=True)

    @property
    def response_html(self) -> str:
        if self.response is None:
            return "-"
        html = "<ol>{}</ol"
        inner_html = ""
        for key, val in self.response.items():
            key = " ".join([(k[0].upper() + k[1:]) for k in key.split('_')])
            inner_html += "<li>{}: <b>{}</b></li>".format(key, val)
        return html.format(inner_html)


class DelhiveryResponse(models.Model):
    pincode = models.CharField(max_length=6, primary_key=True, unique=True)
    response = JSONField(null=True, blank=True)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True)

    @classmethod
    def verify(cls, pincode):
        if not pincode.isdigit() or not len(pincode) == 6:
            return False, {
                "status": "pincode_invalid",
                "status_text": "Invalid Pincode"
            }

        if pincode[:2] not in ['67', '68', '69']:
            return False, {
                "status": "no_delivery_available_outside_kerala",
                "status_text": "Currently we are delivering only inside Kerala! Soon we might Reach There!"
            }
        existing_pincode = cls.objects.filter(pincode=pincode).first()
        if existing_pincode:
            return existing_pincode.status, existing_pincode.response
        from couriers.delhivery.facade import Delhivery
        delhivery = Delhivery()
        response = delhivery.pincode_servicibility(pincode)
        instance = cls.objects.create(
            response=(response or {
                'status_text': 'We could not Deliver to this Location',
                'status': 'could_not_deliver_to_location',
            }),
            pincode=pincode,
            status=(response and response['pre_paid'] == 'Y') or False
        )
        return instance.status, instance.response






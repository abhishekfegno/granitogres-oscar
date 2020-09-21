
# https://groups.google.com/forum/#!topic/django-oscar/H4tf20ujm8k

# from oscar.apps.shipping.repository import *
from decimal import Decimal as D

from django.conf import settings
from oscar.apps.shipping.methods import Free, FixedPrice, NoShippingRequired
from oscar.apps.shipping.repository import Repository as CoreRepository
from oscar.apps.shipping import methods, models
from oscar.apps.shipping.models import WeightBased
from django.utils.translation import ugettext_lazy as _
from django.contrib import messages
from oscar.core import prices


class OwnDeliveryKerala(methods.FixedPrice):
    code = "free-shipping"
    name = _("Own Delivery")

    def calculate(self, basket):
        if basket.total_incl_tax < settings.MINIMUM_BASKET_AMOUNT_FOR_FREE_DELIVERY:
            return prices.Price(
                currency=basket.currency,
                excl_tax=settings.DELIVERY_CHARGE,
                incl_tax=settings.DELIVERY_CHARGE)
        return prices.Price(
            currency=basket.currency,
            excl_tax=self.charge_excl_tax,
            incl_tax=self.charge_incl_tax)


class Repository(CoreRepository):
    """
    This class is included so that there is a choice of shipping methods.
    Oscar's default behaviour is to only have one.
    """

    methods = [OwnDeliveryKerala()]  # init shipping method to default hand delivery

    def get_available_shipping_methods(self, basket, user=None, shipping_addr=None, request=None, **kwargs):
        if shipping_addr:
            if shipping_addr.country.code == 'IN':
                if shipping_addr.postcode[:2] in ['67', '68', '69']:
                    return [OwnDeliveryKerala()]
        return []



# https://groups.google.com/forum/#!topic/django-oscar/H4tf20ujm8k

# from oscar.apps.shipping.repository import *
from decimal import Decimal as D
from oscar.apps.shipping.methods import Free, FixedPrice, NoShippingRequired
from oscar.apps.shipping.repository import Repository as CoreRepository
from oscar.apps.shipping import methods, models
from oscar.apps.shipping.models import WeightBased
from django.utils.translation import ugettext_lazy as _
from django.contrib import messages


class WoodNCartDeliveryKerala(methods.FixedPrice):  # hand delivery, eg for customers located near company premises
    code = "hand-delivery"
    name = _("Hand Delivery")
    charge_excl_tax = D('00.00')


class WoodNCartDeliveryOutsideIndia(methods.FixedPrice):  # hand delivery, eg for customers located near company premises
    code = "hand-delivery"
    name = _("Hand Delivery")
    charge_excl_tax = D('00.00')


class Repository(CoreRepository):
    """
    This class is included so that there is a choice of shipping methods.
    Oscar's default behaviour is to only have one.
    """

    methods = [WoodNCartDeliveryKerala()]  # init shipping method to default hand delivery

    def get_available_shipping_methods(self, basket, user=None, shipping_addr=None, request=None, **kwargs):
        # check if shipping method(s) is available for shipping country (for instance 'FR')
        if shipping_addr:
            # retrieve shipping method(s) for shipping country
            weightbased_set = WeightBased.objects.all().filter(countries=shipping_addr.country.code)
            # set shipping method(s) if available for shipping country
            if weightbased_set:
                methods = (list(weightbased_set))
                methods += [WoodNCartDeliveryKerala()]
            else:
                # no shipping method is available for shipping country, error message will be displayed by oscar core
                methods = []
        # no shipping address, set shipping method to default hand delivery
        else:
            methods = [WoodNCartDeliveryKerala()]
        return methods


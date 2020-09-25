from sqlite3 import IntegrityError

from django import forms
from django.conf import settings
from oscar.core import prices
from oscarapi.basket.operations import assign_basket_strategy
from oscarapi.serializers.checkout import UserAddressSerializer as CoreUserAddressSerializer, UserAddress
from oscarapicheckout.serializers import (
    CheckoutSerializer as OscarAPICheckoutSerializer,
    PaymentMethodsSerializer as OscarAPIPaymentMethodsSerializer,
)
from rest_framework import serializers, exceptions

from apps.availability.zones.facade import ZoneFacade
from apps.availability.zones.serializers import DeliverabilityCheckSerializer, PointSerializer
from apps.mod_oscarapi.calculators import OrderTotalCalculator
from apps.users.models import Location


class PaymentMethodsSerializer(OscarAPIPaymentMethodsSerializer):
    """
    Should not Remove this.
    Dependiences Created.
    """
    pass


class CheckoutSerializer(OscarAPICheckoutSerializer):
    """
    Should not Remove this.
    Dependiences Created.
    """

    def __init__(self, *args, **kwargs):
        super(CheckoutSerializer, self).__init__(*args, **kwargs)
        self.fields['payment'] = PaymentMethodsSerializer(context=kwargs['context'])

    def lookup_annonymous(self, attrs, request):
        if request.user.is_anonymous:
            if not settings.OSCAR_ALLOW_ANON_CHECKOUT:
                message = "Anonymous checkout forbidden"
                raise serializers.ValidationError(message)
            if not attrs.get("guest_email"):
                # Always require the guest email field if the user is anonymous
                message = "Guest email is required for anonymous checkouts"
                raise serializers.ValidationError(message)
        else:
            if "guest_email" in attrs:
                # Don't store guest_email field if the user is authenticated
                del attrs["guest_email"]
        return attrs

    def validate(self, attrs):
        request = self.context["request"]
        attrs = self.lookup_annonymous(attrs, request)
        basket = attrs.get("basket")
        attrs["user"] = basket.owner or (request.user.is_authenticated and request.user) or None
        basket = assign_basket_strategy(basket, request)
        if basket.num_items <= 0:
            message = "Cannot checkout with empty basket"
            raise serializers.ValidationError(message)

        shipping_method = self._shipping_method(
            request,
            basket,
            attrs.get("shipping_method_code"),
            attrs.get("shipping_address"),
        )
        shipping_charge = shipping_method.calculate(basket)
        posted_shipping_charge = attrs.get("shipping_charge")

        if posted_shipping_charge is not None:
            posted_shipping_charge = prices.Price(**posted_shipping_charge)
            # test submitted data.
            if not posted_shipping_charge == shipping_charge:
                message = (
                        "Shipping price incorrect %s != %s"
                        % (posted_shipping_charge, shipping_charge)
                )
                raise serializers.ValidationError(message)

        posted_total = attrs.get("total")
        total = OrderTotalCalculator().calculate(basket, shipping_charge)
        if posted_total is not None:
            if posted_total != total.incl_tax:
                message = ("Total incorrect %s != %s" % (posted_total, total.incl_tax))
                raise serializers.ValidationError(message)
        # update attrs with validated data.
        attrs["order_total"] = total
        attrs["total"] = total
        attrs["shipping_method"] = shipping_method
        attrs["shipping_charge"] = shipping_charge
        attrs["basket"] = basket
        return attrs


class UserAddressSerializer(CoreUserAddressSerializer):
    location = PointSerializer(required=True, write_only=True)
    location_data = serializers.SerializerMethodField()

    def get_location_data(self, instance):
        distance = None
        if self.context['request'] and self.context['request'].session.get('location') and instance.location:
            location_id = self.context['request'].session.get('location')
            loc_obj = Location.objects.filter(pk=location_id).last()
            if loc_obj:
                distance = loc_obj.location.distance(instance.location).m
        return {
            **instance.location_data,
            'distance': distance,
        }

    def validate(self, attrs):
        attrs = super(UserAddressSerializer, self).validate(attrs)
        attrs['location'] = attrs['location']['point']
        zone = ZoneFacade().check_deliverability(point=attrs['location'])
        if not zone:
            raise forms.ValidationError("Currently we are not delivering to this location.")
        return attrs

    class Meta:
        model = UserAddress
        fields = (
            "id",
            "title",
            "first_name",
            "last_name",
            "line1",
            "line2",
            "line3",
            "line4",
            "state",
            "postcode",
            "search_text",
            "phone_number",
            "notes",
            "country",
            "url",
            "location",
            "location_data",
        )

from django.conf import settings
from oscar.apps.partner.availability import Unavailable
from oscar.core.loading import get_model, get_class
from oscar.core.utils import get_default_currency
from oscar.templatetags.currency_filters import currency
from oscarapi.utils.loading import get_api_classes
from rest_framework import serializers

from apps.api_set.serializers.catalogue import custom_ProductListSerializer
from apps.api_set.serializers.mixins import ProductPrimaryImageFieldMixin
from apps.mod_oscarapi.calculators import OrderTotalCalculator
from lib.currencies import get_symbol

Basket = get_model("basket", "Basket")
Line = get_model("basket", "Line")
Product = get_model("catalogue", "Product")
Repository = get_class("shipping.repository", "Repository")
(
    BasketSerializer,
    BasketLineSerializer,
) = get_api_classes(
    "serializers.basket",
    [
        "BasketSerializer",
        "BasketLineSerializer",
    ],
)


class WncProductThumbnailSerializer(ProductPrimaryImageFieldMixin, serializers.ModelSerializer):
    primary_image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = 'id', 'name', 'primary_image'


class WncLineSerializer(BasketLineSerializer):
    product = serializers.SerializerMethodField()
    stockrecord = serializers.SlugRelatedField(slug_field='pk', read_only=True)
    warning = serializers.SerializerMethodField()

    def get_product(self, instance):
        product = instance.product.parent if instance.product.is_child else instance.product
        data = custom_ProductListSerializer([product, ], context=self.context).data
        data = data[0]
        variants = []
        for item in data['variants']:
            item['is_selected'] = item['id'] == instance.product_id
            variants.append(item)
        data['variants'] = variants
        return data

    def get_warning(self, instance):
        if isinstance(instance.purchase_info.availability, Unavailable):
            return "'%(product)s' is no longer available"

    class Meta:
        model = Line

        fields = (
            'id', 'url', 'quantity', 'warning', 'product', 'attributes',
            'price_currency', 'price_excl_tax', 'price_incl_tax',
            'price_incl_tax_excl_discounts', 'price_excl_tax_excl_discounts',
            'is_tax_known', 'warning', 'stockrecord', 'date_created',
        )


class WncBasketSerializer(BasketSerializer):
    lines = serializers.SerializerMethodField()
    currency = serializers.SerializerMethodField()
    shipping = serializers.SerializerMethodField()
    net_total = serializers.SerializerMethodField()
    currency_symbol = serializers.SerializerMethodField()

    shipping_cost = None
    total_amt = None

    def get_shipping_instance(self, basket):
        instance = basket
        if self.context['request'].user.is_authenticated:
            shipping_address = self.context['request'].user.default_shipping_address
        else:
            shipping_address = None
        ship = Repository().get_default_shipping_method(
            basket=instance, shipping_addr=shipping_address,
        )
        self.shipping_cost = ship.calculate(instance)
        self.total_amt = OrderTotalCalculator(request=self.context['request']).calculate(instance, self.shipping_cost)

    def get_lines(self, instance):

        return WncLineSerializer(instance.lines.all(), context=self.context, many=True).data

    def get_currency(self, instance):
        return instance.currency or get_default_currency()

    def get_shipping(self, instance):
        if not self.shipping_cost:
            self.get_shipping_instance(instance)
        return self.shipping_cost.__dict__

    def get_net_total(self, instance):
        if not self.total_amt:
            self.get_shipping_instance(instance)
        return self.total_amt.__dict__

    def get_currency_symbol(self, instance):
        return get_symbol(instance.currency)

    class Meta:
        model = Basket
        fields = (
            "id",
            "status",
            "lines",
            "url",
            "shipping",
            "net_total",
            "currency",
            "currency_symbol",
            "voucher_discounts",
            "offer_discounts",
            "is_tax_known",
        )

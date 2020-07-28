from oscar.core.loading import get_model, get_class
from oscarapi.utils.loading import get_api_classes
from rest_framework import serializers

from apps.api_set.serializers.catalogue import custom_ProductListSerializer
from apps.api_set.serializers.mixins import ProductPrimaryImageFieldMixin

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
        fields = 'id',  'name', 'primary_image'


class WncLineSerializer(BasketLineSerializer):
    product = serializers.SerializerMethodField()
    stockrecord = serializers.SlugRelatedField(slug_field='pk', read_only=True)
    product_variants = serializers.SerializerMethodField()

    def get_product(self, instance):
        product_as_qs = Product.objects.filter(id=instance.product_id)
        return custom_ProductListSerializer(product_as_qs, context=self.context).data

    def get_product_variants(self, instance):
        product_id = instance.product.parent_id if instance.product.parent_id else instance.product_id
        product_as_qs = Product.objects.filter(id=product_id)
        return custom_ProductListSerializer(product_as_qs, context=self.context).data

    class Meta:
        model = Line

        fields = (
            'id',  'url', 'quantity', 'product', 'attributes',
            'price_currency', 'price_excl_tax', 'price_incl_tax',
            'price_incl_tax_excl_discounts', 'price_excl_tax_excl_discounts',
            'is_tax_known', 'warning', 'stockrecord', 'date_created', 'product_variants',
        )


class WncBasketSerializer(BasketSerializer):
    lines = serializers.SerializerMethodField()

    def get_lines(self, instance):
        return WncLineSerializer(instance.lines.all(), context=self.context, many=True).data

    class Meta:
        model = Basket
        fields = (
            "id",
            "status",
            "lines",
            "url",
            "total_excl_tax",
            "total_excl_tax_excl_discounts",
            "total_incl_tax",
            "total_incl_tax_excl_discounts",
            "total_tax",
            "currency",
            "voucher_discounts",
            "offer_discounts",
            "is_tax_known",
        )


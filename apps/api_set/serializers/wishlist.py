from oscar.apps.wishlists.models import WishList, Line
from rest_framework import serializers
from rest_framework.reverse import reverse

from apps.api_set.serializers.mixins import ProductPrimaryImageFieldMixin, ProductPriceFieldMixin


class WishListLineSerializer(ProductPrimaryImageFieldMixin, ProductPriceFieldMixin, serializers.ModelSerializer):
    product = serializers.SerializerMethodField()

    def get_product(self, instance):

        return {
            'id': instance.product_id,
            'image': self.get_primary_image(instance.product),
            'price': self.get_price(instance.product),
            'url': self.context['request'].build_absolute_uri(
                reverse("product-detail", kwargs={'pk': instance.product_id})
            )
        }

    def get_product_image(self, instance):
        return self.get_primary_image(instance.product)

    class Meta:
        model = Line
        fields = ('id', 'product', 'quantity', 'get_title')


class WishListSerializer(serializers.ModelSerializer):
    lines = WishListLineSerializer(many=True, )

    class Meta:
        model = WishList
        fields = ('name', 'key', 'lines')



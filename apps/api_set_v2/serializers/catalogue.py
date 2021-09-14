from rest_framework import serializers
from rest_framework.reverse import reverse

from apps.api_set.serializers.catalogue import custom_ProductListSerializer
from apps.api_set.serializers.mixins import ProductDetailSerializerMixin
from apps.api_set_v2.serializers.mixins import ProductPrimaryImageFieldMixin, ProductPriceFieldMixinLite, \
    ProductAttributeFieldMixin
from apps.catalogue.models import Category, Product


class CategorySerializer(serializers.ModelSerializer):
    icon = serializers.SerializerMethodField()

    def get_icon(self, instance):
        return self.context['request'].build_absolute_uri(instance.icon_thumb_mob)

    class Meta:
        model = Category
        fields = (
            'name',
            'slug',
            'icon',
        )


class ProductSimpleListSerializer(ProductPrimaryImageFieldMixin, ProductPriceFieldMixinLite,
                                  serializers.ModelSerializer):
    primary_image = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    weight = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()

    def get_url(self, instance):
        return reverse('product-detail', kwargs={'pk': instance.pk}, request=self.context.get('request'))

    def get_weight(self, instance):
        if instance.is_parent:
            return None
        if hasattr(instance.attr, 'weight'):
            return getattr(instance.attr, 'weight')
        return 'N/A'

    class Meta:
        model = Product
        fields = ('id', 'title', 'primary_image', 'price', 'weight', 'url')


class ProductDetailWebSerializer(ProductPriceFieldMixinLite, ProductAttributeFieldMixin, ProductDetailSerializerMixin, serializers.ModelSerializer):
    price = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    categories = serializers.SerializerMethodField()
    recommended_products = serializers.SerializerMethodField()
    attributes = serializers.SerializerMethodField()
    variants = serializers.SerializerMethodField()
    product_class = serializers.SerializerMethodField()
    url = serializers.HyperlinkedIdentityField(view_name="product-detail")

    def get_product_class(self, instance):
        return {
            "id": instance.product_class.id,
            "name": instance.product_class.name,
            "slug": instance.product_class.slug,
        }

    class Meta:
        model = Product
        fields = (
            "id",
            "url",
            "title",
            "description",
            "structure",
            "recommended_products",
            "attributes",
            "categories",
            "product_class",
            "images",
            "price",
            "options",
            "variants",
        )

    def get_recommended_products(self, instance):
        # inst = instance.parent if instance.is_child else instance
        inst = instance
        from apps.api_set.serializers.catalogue import ProductSimpleListSerializer
        return ProductSimpleListSerializer(
            inst.sorted_recommended_products,
            many=True,
            context=self.context
        ).data

    def get_variants(self, instance):
        from django.db import connection
        start = len(connection.queries)
        if instance.is_parent:
            data = custom_ProductListSerializer(instance.children.all(), self.context).data
            end = len(connection.queries)
            print("QUERIES CALLED : ", end - start)
            return data
        if instance.is_child:
            data = custom_ProductListSerializer(instance.parent.children.all(), self.context).data
            end = len(connection.queries)
            print("QUERIES CALLED : ", end - start)
            return data
        return

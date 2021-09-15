import math
from decimal import Decimal

from django.core.cache import cache
from django.db.models import Max, F, ExpressionWrapper, IntegerField, Q, Case, When
from django.utils.html import strip_tags
from oscar.apps.offer.models import ConditionalOffer
from oscar.apps.shipping.scales import Scale
from oscar.core.loading import get_model
from oscarapi.utils.loading import get_api_class
from rest_framework import serializers
from rest_framework.relations import HyperlinkedIdentityField
from rest_framework.reverse import reverse

from apps.api_set.serializers.mixins import ProductAttributeFieldMixin, ProductDetailSerializerMixin, \
    ProductPriceFieldMixin, ProductPrimaryImageFieldMixin, ProductPriceFieldMixinLite, \
    SibblingProductAttributeFieldMixin
from apps.catalogue.models import Product, Category, ProductCategory
from apps.dashboard.custom.models import OfferBanner
from apps.partner.models import StockRecord
from lib.cache import cache_library

ProductClass = get_model("catalogue", "ProductClass")
ProductAttributeValue = get_model("catalogue", "ProductAttributeValue")
CategoryField = get_api_class("serializers.fields", "CategoryField")
ProductAttributeValueSerializer = get_api_class('serializers.product', 'ProductAttributeValueSerializer')
OptionSerializer = get_api_class('serializers.product', 'OptionSerializer')
AvailabilitySerializer = get_api_class('serializers.product', 'AvailabilitySerializer')


class FakeSerializerForCompatibility(object):

    def __init__(self, data):
        self.data = data


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = (
            'name',
            'slug',
            'img_thumb_mob',
            # 'offers_upto',
            'description',
            'children',
        )

    children = serializers.SerializerMethodField()
    img_thumb_mob = serializers.SerializerMethodField()
    # offers_upto = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()

    def get_description(self, instance):
        return strip_tags(instance.description)

    def get_children(self, instance):
        return self.__class__(
            instance.get_children(),
            many=True,
            context={'request': self.context['request']}
        ).data or None

    def get_img_thumb_mob(self, instance):
        img = instance.img_thumb_mob
        req = self.context['request']
        return req.build_absolute_uri(img)

    def get_offers_upto(self, instance):
        round_off_base = 5
        if instance.depth == 1:
            field_1 = 'price_excl_tax'
            field_2 = 'price_retail'
            all_nested_categories_from_mp_node = instance.get_descendants_and_self()

            qs = ProductCategory.objects.filter(category__in=all_nested_categories_from_mp_node).values_list(
                'product_id', flat=True)
            qs_filter = Q(product_id__in=qs)

            sr = StockRecord.objects.filter(qs_filter).only('id')  # get queryset
            sr2 = sr.annotate(
                diff_percentage=ExpressionWrapper(  # wrap expression : (field_1 - field_2) * 100 / field_1
                    Case(
                        When(**{f'{field_1}__gt': 0}, then=(F(field_1) - F(field_2)) * Decimal('100.0') / (F(field_1))), default=0
                    ),
                    output_field=IntegerField())
            )

            percent = sr2.aggregate(Max('diff_percentage'))['diff_percentage__max'] or 0
            if percent:
                return round_off_base * math.ceil(percent/round_off_base)     # to round 43 to 45 and 46 to 50
        return 0


class ProductSimpleListSerializer(ProductPrimaryImageFieldMixin, serializers.ModelSerializer):
    primary_image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ('id', 'parent', 'title', 'slug', 'primary_image',)


class ProductListSerializer(ProductPrimaryImageFieldMixin, ProductPriceFieldMixinLite, serializers.ModelSerializer):
    primary_image = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    url = serializers.HyperlinkedIdentityField(view_name="product-detail")

    class Meta:
        model = Product
        fields = ('id', 'title', 'rating', 'num_approved_reviews',
                  'primary_image', 'url', 'price')


def custom_ProductListSerializer(queryset, context,
                                 price_serializer_mixin=ProductPriceFieldMixinLite(),
                                 primary_image_serializer_mixin=ProductPrimaryImageFieldMixin(), **kwargs):
    request = context['request']
    primary_image_serializer_mixin.context = context
    price_serializer_mixin.context = context

    def _solve(product):
        nonlocal queryset, request, primary_image_serializer_mixin, price_serializer_mixin

        return {
            "id": product.id,
            "title": product.title,
            "feature": product.title.split("-")[-1],
            "primary_image": primary_image_serializer_mixin.get_primary_image(product),
            "url": request.build_absolute_uri(
                reverse('product-detail', kwargs={'pk': product.id})
            ),
            "price": price_serializer_mixin.get_price(product),
            "is_meet": product.is_meet,
            "is_vegetarian": product.is_vegetarian,
            "weight": getattr(
                product.attribute_values.filter(attribute__code='weight').first(), 'value', 'unavailable'
            ) if not product.is_parent else None,
            'variants': custom_ProductListSerializer(product.children.all(), context,
                                                     price_serializer_mixin=price_serializer_mixin,
                                                     primary_image_serializer_mixin=primary_image_serializer_mixin).data,
        }
    result = []
    for product in queryset:
        cache_key = f"___custom_ProductListSerializer__cached__product:{product.id}__zone_v1:{request.session.get('zone', '0')}"
        data = cache_library(cache_key, cb=lambda: _solve(product))
        cache.delete(cache_key)
        result.append(data)

        # keeping original serializer compatibility so that they can take data as serializer(queryset, context).data
    return FakeSerializerForCompatibility(result)


class ProductListSerializerExpanded(ProductPriceFieldMixin, ProductListSerializer):
    pass


class SiblingProductsSerializer(SibblingProductAttributeFieldMixin, ProductListSerializer):
    attributes = serializers.SerializerMethodField()
    url = serializers.HyperlinkedIdentityField(view_name="product-detail")

    class Meta:
        model = Product
        fields = ('title', 'slug', 'attributes', 'url')


class ProductDetailWebSerializer(ProductAttributeFieldMixin, ProductPriceFieldMixinLite,
                                 ProductDetailSerializerMixin, serializers.ModelSerializer):
    price = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    categories = serializers.SerializerMethodField()
    recommended_products = serializers.SerializerMethodField()
    attributes = serializers.SerializerMethodField()
    product_class = serializers.SlugRelatedField(slug_field="slug", queryset=ProductClass.objects, allow_null=True)
    options = OptionSerializer(many=True, required=False)
    variants = serializers.SerializerMethodField()
    url = serializers.HyperlinkedIdentityField(view_name="product-detail")
    about = serializers.SerializerMethodField()
    storage_and_uses = serializers.SerializerMethodField()
    benifits = serializers.SerializerMethodField()
    other_product_info = serializers.SerializerMethodField()
    variable_weight_policy = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            "id",
            'url',
            # "slug",
            "title",
            # "upc",
            # 'rating',
            # 'num_approved_reviews',
            "description",
            "structure",
            "recommended_products",
            "attributes",
            "categories",
            "product_class",
            "images",
            "price",
            "options",
            # "siblings",
            "variants",
            'is_meet',
            'is_vegetarian',
            'about',
            'storage_and_uses',
            'benifits',
            'other_product_info',
            'variable_weight_policy',
            # 'deliverable',
        )

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


class ProductDetailMobileSerializer(ProductListSerializer, serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ('structure', 'parent', 'name', 'slug', 'rating', 'num_approved_reviews',
                  'effective_price', 'retail_price')


class ConditionalOfferLiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConditionalOffer
        fields = ('pk', 'name', 'end_datetime', 'max_discount', 'max_user_applications', 'exclusive', 'offer_type')


class SimpleOfferBannerSerializer(serializers.ModelSerializer):
    offer = ConditionalOfferLiteSerializer()
    url = HyperlinkedIdentityField(view_name='api-offer-products', lookup_field='code', lookup_url_kwarg='slug')

    class Meta:
        model = OfferBanner
        fields = ('code', 'name', 'offer', 'banner', 'url')

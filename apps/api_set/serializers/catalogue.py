from oscar.apps.offer.models import ConditionalOffer
from oscar.core.loading import get_model
from oscarapi.utils.loading import get_api_class
from rest_framework import serializers
from rest_framework.relations import HyperlinkedIdentityField
from rest_framework.reverse import reverse

from apps.api_set.serializers.mixins import ProductAttributeFieldMixin, ProductDetailSerializerMixin, \
    ProductPriceFieldMixin, ProductPrimaryImageFieldMixin, ProductPriceFieldMixinLite, \
    SibblingProductAttributeFieldMixin
from apps.catalogue.models import Product, Category
from apps.dashboard.custom.models import OfferBanner

ProductClass = get_model("catalogue", "ProductClass")
CategoryField = get_api_class("serializers.fields", "CategoryField")
ProductAttributeValueSerializer = get_api_class('serializers.product', 'ProductAttributeValueSerializer')
OptionSerializer = get_api_class('serializers.product', 'OptionSerializer')
AvailabilitySerializer = get_api_class('serializers.product', 'AvailabilitySerializer')


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('name', 'thumbnail_web_listing', 'slug', 'numchild', 'depth', 'product_count', 'children', )

    # breadcrumbs = serializers.CharField(source="full_name", read_only=True)
    children = serializers.SerializerMethodField()
    thumbnail_web_listing = serializers.SerializerMethodField()
    product_count = serializers.SerializerMethodField()

    # product_url = serializers.SerializerMethodField()

    def get_children(self, instance):
        return self.__class__(
            instance.get_children(),
            many=True,
            context={'request': self.context['request']}
        ).data

    def get_product_count(self, instance):
        return Product.browsable.browsable().filter(
            id__in=Product.browsable.browsable().filter(
                categories__in=Category.objects.all().filter(path__startswith=instance.path, numchild=0)
            )
        ).count()

    def get_thumbnail_web_listing(self, instance):
        img = instance.thumbnail_web_listing
        req = self.context['request']
        return req.build_absolute_uri(img)


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
        fields = ('id', 'title', 'slug', 'rating', 'num_approved_reviews',
                  'primary_image', 'url', 'price')


class ProductListSerializerExpanded(ProductPriceFieldMixin, ProductListSerializer):
    pass


class SiblingProductsSerializer(SibblingProductAttributeFieldMixin, ProductListSerializer):
    attributes = serializers.SerializerMethodField()
    url = serializers.HyperlinkedIdentityField(view_name="product-detail")

    class Meta:
        model = Product
        fields = ('title', 'slug', 'attributes', 'url')


class ProductDetailWebSerializer(ProductAttributeFieldMixin, ProductPriceFieldMixin,
                                 ProductDetailSerializerMixin, serializers.ModelSerializer):
    price = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    categories = serializers.SerializerMethodField()
    recommended_products = serializers.SerializerMethodField()
    attributes = serializers.SerializerMethodField()
    product_class = serializers.SlugRelatedField(slug_field="slug", queryset=ProductClass.objects, allow_null=True)
    options = OptionSerializer(many=True, required=False)
    siblings = serializers.SerializerMethodField()
    url = serializers.HyperlinkedIdentityField(view_name="product-detail")

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
            "siblings",
            # "additional_product_information",
            # "care_instructions",
            # "customer_redressal",
            # "merchant_details",
            # "returns_and_cancellations",
            # "warranty_and_installation",
        )


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

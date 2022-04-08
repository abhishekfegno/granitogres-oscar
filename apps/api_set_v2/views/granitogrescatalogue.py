from rest_framework.generics import ListAPIView, RetrieveAPIView

from apps.api_set.serializers.mixins import ProductPriceFieldMixinLite, ProductAttributeFieldMixin, \
    ProductDetailSerializerMixin
from rest_framework import serializers

from apps.api_set_v2.serializers.mixins import ProductPrimaryImageFieldMixin
from apps.catalogue.models import Product


class ProductDetailSerializer(ProductPriceFieldMixinLite, ProductAttributeFieldMixin, ProductDetailSerializerMixin,
                                 serializers.ModelSerializer):

    upselling = serializers.SerializerMethodField()
    url = serializers.HyperlinkedIdentityField(view_name="product-detail")

    def get_cimage(self, instance):
        return instance.product360image_set.all()

    class Meta:
        model = Product
        fields = (
            "id",
            "url",
            "title",
            "description",
            "seo_title",
            "seo_description",
            "seo_keywords",
            "structure",
            "recommended_products",
            "attributes",
            "categories",
            # "product_class",
            "images",
            "price",
            # "options",
            # "variants",
            # "siblings",
            # 'rating',
            # 'rating_split',
            'brand',
            # 'review_count',
            # 'reviews',
            # 'breadcrumb',
            'upselling',
            'crossselling',

            'cimage',
                  )


class ProductListSerializer(ProductPrimaryImageFieldMixin, ProductPriceFieldMixinLite,
                                  serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = (
            'id', 'title', 'structure', 'primary_image', 'price', 'weight', 'url', 'rating', 'review_count', 'brand',
            'search_tags')


class ProductDetailview(RetrieveAPIView):
    serializer_class = ProductDetailSerializer
    queryset = Product.objects.all()


class ProductListView(ListAPIView):
    serializer_class = ProductListSerializer
    queryset = Product.objects.all()

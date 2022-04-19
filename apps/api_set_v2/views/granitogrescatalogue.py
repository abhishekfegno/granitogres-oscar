from django.conf import settings
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.reverse import reverse

from apps.api_set.serializers.mixins import ProductPriceFieldMixinLite, ProductAttributeFieldMixin, \
    ProductDetailSerializerMixin
from rest_framework import serializers, status

from apps.api_set_v2.serializers.mixins import ProductPrimaryImageFieldMixin
from apps.catalogue.models import Product
from apps.utils import dummy_purchase_info_lite_as_dict, purchase_info_lite_as_dict
from apps.utils import get_purchase_info, purchase_info_as_dict, purchase_info_lite_as_dict, image_not_found


class ProductDetailSerializer(ProductPriceFieldMixinLite, ProductAttributeFieldMixin, ProductDetailSerializerMixin,
                                 serializers.ModelSerializer):

    # upselling = serializers.SerializerMethodField()
    url = serializers.HyperlinkedIdentityField(view_name="product-detail")
    # price = serializers.SerializerMethodField()
    cimage = serializers.SerializerMethodField()

    def get_cimage(self, instance):
        if instance.product360image_set:
            return {
                "image": self.context['request'].build_absolute_uri(instance.product360image_set.first().image.url)
            }
        else:
            print(settings.MEDIA_URL + '/product360/360.jpg')
            return settings.MEDIA_URL + '/product360/360.jpg'


    # def get_price(self, product):
    #     key = 'ProductPriceFieldMixinLite__{0}__{1}'
    #
    #     def _inner():
    #         if product.is_parent:
    #             return dummy_purchase_info_lite_as_dict(availability=False, availability_message='')
    #         purchase_info = get_purchase_info(product, request=self.context['request'])  # noqa: mixin ensures
    #         addittional_informations = {
    #             "availability": bool(purchase_info.availability.is_available_to_buy),
    #             "availability_message": purchase_info.availability.short_message,
    #         }
    #         return purchase_info_lite_as_dict(purchase_info, **addittional_informations)
    #
    #     return _inner()

    class Meta:
        model = Product
        fields = (
            "id",
            "url",
            "title",
            "slug",
            "description",
            "seo_title",
            "seo_description",
            "seo_keywords",
            "structure",
            "recommended_products",
            "attributes",
            "categories",
            # "product_class",
            # "images",
            "effective_price",
            # "price",
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

    # price = serializers.SerializerMethodField()
    primary_image = serializers.SerializerMethodField()

    # def get_url(self, instance):
    #     return reverse('product-detail', kwargs={'slug': instance.slug}, request=self.context.get('request'))

    # def get_price(self, product):
    #     key = 'ProductPriceFieldMixinLite__{0}__{1}'
    #
    #     def _inner():
    #         if product.is_parent:
    #             return dummy_purchase_info_lite_as_dict(availability=False, availability_message='')
    #         purchase_info = get_purchase_info(product, request=self.context['request'])  # noqa: mixin ensures
    #         addittional_informations = {
    #             "availability": bool(purchase_info.availability.is_available_to_buy),
    #             "availability_message": purchase_info.availability.short_message,
    #         }
    #         return purchase_info_lite_as_dict(purchase_info, **addittional_informations)
    #
    #     return _inner()

    class Meta:
        model = Product
        fields = (
            'id', 'title', 'structure', 'primary_image', "effective_price", 'weight', 'url', 'rating',
            'review_count', 'brand', 'search_tags')


class ProductDetailview(RetrieveAPIView):
    serializer_class = ProductDetailSerializer
    queryset = Product.objects.all()

    def get(self, request, *args, **kwargs):
        qs = self.get_queryset().filter(slug=kwargs.get('slug'))
        serializer = self.serializer_class(qs, context={'request': request}, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProductListView(ListAPIView):
    serializer_class = ProductListSerializer
    queryset = Product.objects.all()

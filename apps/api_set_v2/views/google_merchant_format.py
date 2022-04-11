import timeit
from django.core.cache import cache
from typing import Union, Any
from django.conf import settings
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db import models, connection
from django.db.models import Q, Value, Prefetch
from django.http import Http404
from django.shortcuts import redirect
from oscar.apps.offer.models import Range
from rest_framework import serializers
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.viewsets import ModelViewSet

from apps.api_set_v2.serializers.catalogue import ProductSimpleListSerializer
from apps.api_set_v2.serializers.mixins import ProductPrimaryImageFieldMixin, ProductPriceFieldMixinLite
from apps.api_set_v2.views.product_listing_query_pagination import get_breadcrumb
from django.utils.translation import ugettext as _

from apps.availability.models import Zones
from apps.catalogue.models import Product, ProductClass
from apps.partner.models import StockRecord
from apps.utils.urls import list_api_formatter
from lib.product_utils import category_filter, recommended_class, apply_filter, apply_search, apply_sort

from factory.django import get_model
from oscar.apps.offer.models import ConditionalOffer
from oscar.apps.search.signals import user_search
from oscar.core.loading import get_class
from rest_framework.decorators import api_view
from rest_framework.generics import get_object_or_404, GenericAPIView
from rest_framework.response import Response
from apps.api_set.serializers.catalogue import (
    custom_ProductListSerializer
)
from apps.api_set_v2.utils.product import get_optimized_product_dict
from apps.availability.models import Zones
from apps.dashboard.custom.models import OfferBanner
from apps.partner.models import StockRecord
from lib.product_utils import category_filter, apply_filter, apply_search, apply_sort, recommended_class
from apps.catalogue.models import Product
from apps.utils.urls import list_api_formatter
from lib import cache_key
from lib.cache import cache_library
from lib.product_utils.search import tag__combinations
from shopping.content.products.google_merchant_api import merchant_api

get_product_search_handler_class = get_class(
    'catalogue.search_handlers', 'get_product_search_handler_class')

_ = lambda x: x

Category = get_model('catalogue', 'Category')

# sorting

RELEVANCY = "relevancy"
TOP_RATED = "rating"
NEWEST = "newest"
PRICE_HIGH_TO_LOW = "price-desc"
PRICE_LOW_TO_HIGH = "price-asc"
TITLE_A_TO_Z = "title-asc"
TITLE_Z_TO_A = "title-desc"

SORT_BY_CHOICES = [
    (RELEVANCY, _("Relevancy")), (TOP_RATED, _("Customer rating")), (NEWEST, _("Newest")),
    (PRICE_HIGH_TO_LOW, _("Price high to low")), (PRICE_LOW_TO_HIGH, _("Price low to high")),
    (TITLE_A_TO_Z, _("Title A to Z")), (TITLE_Z_TO_A, _("Title Z to A")),
]

SORT_BY_MAP = {
    TOP_RATED: '-rating', NEWEST: '-date_created', PRICE_HIGH_TO_LOW: '-effective_price',
    PRICE_LOW_TO_HIGH: 'effective_price', TITLE_A_TO_Z: 'title', TITLE_Z_TO_A: '-title',
}

# FILTERING
FILTER_BY_CHOICES = [
    ('exclude_out_of_stock', "Exclude Out Of Stock"),
    ('price__range', "Price Range"),
    ('width', "Width"),
    ('height', "Height"),
    ('material', 'Material'),
]


class MerchantProductListSerializer(ProductPrimaryImageFieldMixin,
                                  serializers.ModelSerializer):
    primary_image = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    weight = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    brand = serializers.SerializerMethodField()

    def get_url(self, instance):
        return reverse('product-detail', kwargs={'pk': instance.pk}, request=self.context.get('request'))

    def get_brand(self, instance):
        return instance.get_brand_name()

    def get_weight(self, instance):
        if instance.is_parent:
            return None
        if hasattr(instance.attr, 'weight'):
            return getattr(instance.attr, 'weight')
        return 'N/A'

    def get_price(self, instance):
        return instance.effective_price or '0.00'

    class Meta:
        model = Product
        fields = (
            'id', 'title', 'structure', 'primary_image', 'price', 'weight', 'url', 'rating', 'review_count', 'brand',
            'search_tags')


class MerchantListModelViewSet(GenericAPIView):
    pid = StockRecord.objects.filter(product__structure__in=[Product.CHILD, Product.STANDALONE]).values_list('product_id')
    queryset = Product.objects.filter(id__in=pid)[:50]
    serializer_class = MerchantProductListSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})

        return context

    def post(self, request, *args, **kwags):
        data = MerchantProductListSerializer(self.get_queryset(), many=True).data
        message = merchant_api(data)
        print(message)
        # return reverse('dashboard:catalogue-product-list')
        return Response({"message": message})


call_merchant = MerchantListModelViewSet.as_view()

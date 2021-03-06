from collections import OrderedDict

from django.conf import settings
from django.core.cache import cache
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie

from factory.django import get_model
from oscar.apps.offer.models import ConditionalOffer
from oscar.core.loading import get_class
from rest_framework.decorators import api_view
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from apps.api_set.serializers.catalogue import (
    CategorySerializer, ProductListSerializer,
    ProductDetailMobileSerializer, ProductDetailWebSerializer, custom_ProductListSerializer
)
from apps.dashboard.custom.models import OfferBanner
from lib.product_utils import category_filter, apply_filter, apply_search, apply_sort, recommended_class
from apps.catalogue.models import Product, ProductAttribute, AttributeOption
from apps.utils.urls import list_api_formatter
from lib import cache_key
from lib.cache import cache_library

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
    ('exclude_out_of_stock', _("Exclude Out Of Stock")),
    ('price__range', _("Price Range")),
    ('width', _("Width")),
    ('height', _("Height")),
    ('material', _('Material')),
]


def __get_category_cached(request):
    def _inner():
        queryset = Category.get_root_nodes().exclude(slug__in=[settings.FEATURED_CATEGORY_SLUG])
        serializer_class = CategorySerializer
        return {
            'result': serializer_class(queryset, many=True, context={'request': request}).data
        }
    return cache_library(cache_key.categories_list_cached__key, cb=_inner)


@api_view()
def categories_list_cached(request):
    return Response(__get_category_cached(request))




@api_view()
@cache_page(60 * 60 * 2)
@vary_on_cookie
def product_detail_web(request, product):
    queryset = Product.objects.base_queryset()
    serializer_class = ProductDetailWebSerializer
    product = get_object_or_404(queryset, pk=product)
    # if product.is_parent:
    #     focused_product = product.get_apt_child(order='-price_excl_tax')
    focused_product = product
    if product.is_child:
        focused_product = product.parent
        product = product
    return Response({
        'results': serializer_class(instance=focused_product, context={'request': request, 'product': product}).data
    })


def __(val):
    if type(val.value) == AttributeOption:
        return str(val.value)
        # return {str(x) for x in val.options.all().values_list('name', flat=True)}
    else:
        return val.value


def to_client_dict(value_array):
    return [{
        'label': value,
        'is_checked': False
    } for value in value_array]


@api_view()
def filter_options(request, pk):
    attrs = ProductAttribute.objects.filter(
        is_varying=True, product_class__id=pk
    ).prefetch_related('productattributevalue_set')
    return Response({
        'results': [{
            'code': attr.code,
            'label': attr.name,
            'val': to_client_dict({__(value) for value in attr.productattributevalue_set.all()})
        } for attr in attrs if attr.productattributevalue_set.exists()]
    })


@api_view()
def product_suggestions(request, **kwargs):
    queryset = Product.browsable.browsable()
    _search = request.GET.get('q')
    _max_size = 10
    out = {'results': [],   'class': None, }
    if _search:
        queryset = apply_search(queryset=queryset, search=_search)
        rc = recommended_class(queryset)
        queryset = queryset.values('title', 'slug')
        out['results'] = queryset[:_max_size]
        out['class'] = rc

    # return JsonResponse(out, status=(400 if len(out['results']) == 0 else 200))
    return Response(out, status=(400 if len(out['results']) == 0 else 200))



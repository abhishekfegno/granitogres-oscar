from django.conf import settings
from django.core.cache import cache
from django.core.paginator import Paginator
from elasticsearch_dsl.query import Exists

from factory.django import get_model
from haystack.query import EmptySearchQuerySet
from haystack.views import FacetedSearchView
from oscar.apps.offer.models import ConditionalOffer, Range
from oscar.apps.search.facets import base_sqs
from oscar.apps.search.forms import SearchForm, BrowseCategoryForm
from oscar.apps.search.search_handlers import SearchHandler
from oscar.core.loading import get_class
from rest_framework.decorators import api_view
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from apps.api_set.search import GrocerySearchHandler
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
def product_list(request, category='all', **kwargs):
    """
    PRODUCT LISTING API, (powering,  list /c/all/, /c/<category_slug>/,  )
    q = "A search term "
    product_range = '<product-range-id>'
    sort = <depricated>
    filter = <depricated>
    """

    queryset = Product.browsable.browsable().base_queryset()
    serializer_class = custom_ProductListSerializer
    _search = request.GET.get('q')
    _sort = request.GET.get('sort')
    _product_range = request.GET.get('product_range')
    page_number = int(str(request.GET.get('page', 1)))
    page_size = int(str(request.GET.get('page_size', settings.DEFAULT_PAGE_SIZE)))
    search_form_class = BrowseCategoryForm
    out = {
        'query': None,
        'suggestion': None,
        'count': 0,
    }

    if _product_range:
        _product_range_object = get_object_or_404(Range, id=_product_range)
        queryset = _product_range_object.all_products().base_queryset()

    if category != 'all':
        queryset, cat = category_filter(queryset=queryset, category_slug=category)

    # if _search:
    handler = GrocerySearchHandler(request.GET, request.get_full_path(), form_class=search_form_class,
                                   paginate_by=page_size)
    out['query'] = handler.search_form.cleaned_data['q']
    out['suggestion'] = handler.search_form.get_suggestion()
    out['count'] = handler.results.facet_counts()
    def _inner():
        nonlocal handler, queryset, out
        page_obj = handler.paginator.get_page(page_number)
        product_data = serializer_class(page_obj.object_list, context={'request': request}).data
        return list_api_formatter(
            request, page_obj=page_obj,
            results=product_data,
            # product_class=rc,
            **out)

    return Response(_inner())


@api_view()
def product_detail_web(request, product):
    queryset = Product.objects.base_queryset()
    serializer_class = ProductDetailWebSerializer
    product = get_object_or_404(queryset, pk=product)
    if product.is_parent:
        focused_product = product.get_apt_child(order='-price_excl_tax')
    elif product.is_child:
        focused_product = product
        product = product.parent
    else:
        focused_product = product
    return Response({
        'results': serializer_class(instance=focused_product, context={'request': request, 'product': product}).data
    })


@api_view()
def product_detail_mobile(request, product):
    queryset = Product.browsable.filter().prefetch_related('children', 'product_options', 'stockrecords', 'images')
    serializer_class = ProductDetailMobileSerializer
    product = get_object_or_404(queryset, slug=product)
    # if product.is_parent:
    #     product = product.get_apt_child(order='-price_excl_tax')

    return Response({
        'results': serializer_class(instance=product).data
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



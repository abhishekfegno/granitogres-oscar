from django.conf import settings
from django.core.cache import cache
from django.core.paginator import Paginator

from factory.django import get_model
from oscar.apps.offer.models import ConditionalOffer
from oscar.core.loading import get_class
from rest_framework.decorators import api_view
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from apps.api_set.serializers.catalogue import (
    CategorySerializer, ProductListSerializer,
    ProductDetailMobileSerializer, ProductDetailWebSerializer
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
def product_list(request, category='all', **kwargs):
    """
    PRODUCT LISTING API, (powering,  list /c/all/, /c/<category_slug>/,  )

    q = " A search term "
    offer_category = '<offer-banner-slug>'
    sort = any one from ['relevancy', 'rating', 'newest', 'price-desc', 'price-asc', 'title-asc', 'title-desc']
    filter = minprice:25::maxprice:45::available_only:1::color=Red,Black,Blue::weight:25,30,35::ram:4 GB,8 GB
        Where minprice, maxprice and  available_only are common for all.
        other dynamic parameters are available at  reverse('wnc-filter-options', kwarg={'pk': '<ProductClass: id>'})

    """

    queryset = Product.browsable.browsable()
    serializer_class = ProductListSerializer
    _search = request.GET.get('q')
    _sort = request.GET.get('sort')
    _filter = request.GET.get('filter')
    _offer_category = request.GET.get('offer_category')
    page_number = int(str(request.GET.get('page', 1)))
    page_size = int(str(request.GET.get('page_size', settings.DEFAULT_PAGE_SIZE)))
    out = {}
    # search_handler = get_product_search_handler_class()(request.GET, request.get_full_path(), [])

    if _offer_category:
        offer_banner_object = get_object_or_404(OfferBanner, code=_offer_category, offer__status=ConditionalOffer.OPEN)
        queryset = offer_banner_object.products().filter(structure__in=['standalone', 'child'], is_public=True, stockrecords__isnull=False)

    if category != 'all':
        queryset = category_filter(queryset=queryset, category_slug=category)

    if _filter:
        """
        input = weight__in:25,30,35|price__gte:25|price__lte:45
        """
        queryset = apply_filter(queryset=queryset, _filter=_filter)

    if _search:
        queryset = apply_search(queryset=queryset, search=_search)

    if _sort:
        _sort = [SORT_BY_MAP[key] for key in _sort.split(',') if key and key in SORT_BY_MAP.keys()]
        queryset = apply_sort(queryset=queryset, sort=_sort)

    def _inner():
        nonlocal queryset
        paginator = Paginator(queryset, page_size)  # Show 18 contacts per page.
        page_obj = paginator.get_page(page_number)
        product_data = serializer_class(page_obj.object_list, many=True, context={'request': request}).data
        rc = None
        if category != 'all':
            rc = recommended_class(queryset)
        return list_api_formatter(request, page_obj=page_obj, results=product_data, product_class=rc)

    # if page_size == settings.DEFAULT_PAGE_SIZE and page_number <= 4 and not _search and not _filter and not _sort:
    #     c_key = cache_key.product_list__key.format(page_number, page_size, category)
    #     if settings.DEBUG:
    #         cache.delete(c_key)
    #     out = cache_library(c_key, cb=_inner)
    # else:
    #     out = _inner()
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



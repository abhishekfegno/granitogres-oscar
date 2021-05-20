from django.core.cache import cache
from oscar.apps.offer.models import ConditionalOffer, Range
from django.conf import settings
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

from factory.django import get_model
from oscar.apps.offer.models import ConditionalOffer
from oscar.core.loading import get_class
from rest_framework.decorators import api_view
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from apps.api_set.serializers.catalogue import (
    custom_ProductListSerializer
)
from apps.api_set_v2.utils.product import get_optimized_product_dict
from apps.dashboard.custom.models import OfferBanner
from lib.product_utils import category_filter, apply_filter, apply_search, apply_sort
from apps.catalogue.models import Product
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


@api_view()
def product_list(request, category='all', **kwargs):
    """
    PRODUCT LISTING API, (powering,  list /c/all/, /c/<category_slug>/,  )

    q = " A search term "
    product_range = '<product-range-id>'
    sort = any one from ['relevancy', 'rating', 'newest', 'price-desc', 'price-asc', 'title-asc', 'title-desc']
    filter = minprice:25::maxprice:45::available_only:1::color=Red,Black,Blue::weight:25,30,35::ram:4 GB,8 GB
        Where minprice, maxprice and  available_only are common for all.
        other dynamic parameters are available at  reverse('wnc-filter-options', kwarg={'pk': '<ProductClass: id>'})
    """

    queryset = Product.browsable.browsable()
    serializer_class = custom_ProductListSerializer
    _search = request.GET.get('q')
    _sort = request.GET.get('sort')
    _filter = request.GET.get('filter')
    _offer_category = request.GET.get('offer_category')
    _product_range = request.GET.get('product_range')
    page_number = int(request.GET.get('page', '1'))
    page_size = int(request.GET.get('page_size', str(settings.DEFAULT_PAGE_SIZE)))
    out = {}
    # search_handler = get_product_search_handler_class()(request.GET, request.get_full_path(), [])

    if _product_range:
        product_range = get_object_or_404(Range, pk=_product_range)
        queryset = product_range.all_products().filter(is_public=True)
    elif _offer_category:
        offer_banner_object = get_object_or_404(OfferBanner, code=_offer_category, offer__status=ConditionalOffer.OPEN)
        queryset = offer_banner_object.products().filter(is_public=True)
    elif category != 'all':
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
        nonlocal queryset, page_number
        # queryset = queryset.browsable().base_queryset()
        paginator = Paginator(queryset, page_size)  # Show 18 contacts per page.
        empty_list = False
        try:
            page_number = paginator.validate_number(page_number)
        except PageNotAnInteger:
            page_number = 1
        except EmptyPage:
            page_number = paginator.num_pages
            empty_list = True
        page_obj = paginator.get_page(page_number)
        if not empty_list:
            product_data = get_optimized_product_dict(qs=page_obj.object_list, request=request).values()
            # product_data = serializer_class(page_obj.object_list, many=True, context={'request': request}).data
        else:
            product_data = []
        rc = None
        return list_api_formatter(request, page_obj=page_obj, results=product_data, product_class=rc)
    if page_size == settings.DEFAULT_PAGE_SIZE and page_number <= 4 and not any([_search, _filter, _sort, _offer_category, _product_range, ]):
        c_key = cache_key.product_list__key.format(page_number, page_size, category)
        # if settings.DEBUG:
        #     cache.delete(c_key)
        out = cache_library(c_key, cb=_inner, ttl=180)
    else:
        out = _inner()
    return Response(out)



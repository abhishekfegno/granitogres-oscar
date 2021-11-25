from django.core.cache import cache
from django.db.models import Q
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
from apps.availability.models import Zones
from apps.dashboard.custom.models import OfferBanner
from apps.partner.models import StockRecord
from lib.product_utils import category_filter, apply_filter, apply_search, apply_sort, recommended_class
from apps.catalogue.models import Product, ProductClass
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


def get_breadcrumb(_search, cat, product_range):
    if cat:
        cats = cat.get_ancestors_and_self()
    else:
        class C:
            name = "All"
            slug = "all"
        cats = [C]
    out = [
        {"title": "Home", "url": '?'},
        *[{"title": c.name, "url": f'?category={c.slug}'} for c in cats],
    ]
    if product_range:
        out.append({"title": product_range.name, "url": f"?product_range={product_range.id}"})
    if _search:
        out.append({"title": f"Search: {_search}", "url": f"?q={_search}"})
    return out


@api_view()
def product_list_pagination(request, category='all', **kwargs):
    """
    PRODUCT LISTING API, (powering,  list /c/all/, /c/<category_slug>/,  )
    ===
    q = " A search term "
    product_range = '<product-range-id>'
    sort = any one from ['relevancy', 'rating', 'newest', 'price-desc', 'price-asc', 'title-asc', 'title-desc']
    filter = weight:25|30|35::minprice:25::maxprice:45::available_only:1::color=Red|Black|Blue::ram:4 GB|8 GB
        Where minprice, maxprice and  available_only are common for all.
        other dynamic parameters are available at  reverse('wnc-filter-options', kwarg={'pk': '<ProductClass: id>'})
    """
    _default_category = 'all'
    queryset = Product.browsable.browsable()
    _search = request.GET.get('q')
    _sort = request.GET.get('sort')
    _filter = request.GET.get('filter')
    _offer_category = request.GET.get('offer_category')
    _range = request.GET.get('range')
    _pclass = request.GET.get('pclass')
    _pincode = request.GET.get('pincode')
    _brand = request.GET.get('brand')

    page_number = int(request.GET.get('page', '1'))
    page_size = int(request.GET.get('page_size', str(settings.DEFAULT_PAGE_SIZE)))
    only_favorite = bool(request.GET.get('only_favorite', False))
    out = {}
    # search_handler = get_product_search_handler_class()(request.GET, request.get_full_path(), [])
    title = 'All'
    product_range = None
    cat = None

    if _range:
        if type(_range) is int or _range.isdigit():
            params = {'id': _range}
        else:
            params = {'slug': _range}
        product_range = Range.objects.filter(**params).first()
        if product_range:
            title = product_range.name
            queryset = product_range.all_products().filter(is_public=True)
    elif _offer_category:
        offer_banner_object = get_object_or_404(OfferBanner, code=_offer_category, offer__status=ConditionalOffer.OPEN)
        if offer_banner_object and offer_banner_object.product_range:
            title = offer_banner_object.product_range.name
            queryset = offer_banner_object.products().filter(is_public=True)
    elif category != _default_category:
        queryset, cat = category_filter(queryset=queryset, category_slug=category, return_as_tuple=True)
        title = cat.name

    params = {'search': _search, 'range': product_range, "category": cat, "pclass": _pclass}
    rc = recommended_class(queryset, **params)
    product_class = ProductClass.objects.filter(pk=rc['id']).first()

    if only_favorite and request.user.is_authenticated:
        queryset = queryset.browsable.filter(id__in=request.user.product.all().values_list('id'))

    if _pclass and (_search or category == _default_category):
        queryset = queryset.filter(Q(product_class_id=_pclass) | Q(parent__product_class_id=_pclass))

    if _filter:
        """
        input = weight__in:25,30,35|price__gte:25|price__lte:45
        """
        queryset = apply_filter(queryset=queryset, _filter=_filter, product_class=product_class)

    if _search:
        # mode = '_simple'
        # if len(_search) <= 2:
        #     mode = '_simple'
        # else:
        #     mode = '_trigram'
        queryset = apply_search(queryset=queryset, search=_search, mode='_simple')  # | apply_search(queryset=queryset, search=_search, mode='_trigram',)
        title = f"Search: '{_search}'"

    def _inner():
        nonlocal queryset, page_number, title, _sort, _pclass
        zone = None
        if request.GET.get('pincode'):
            from apps.availability.facade import get_zone_from_pincode
            _zone = get_zone_from_pincode(request.GET.get('pincode'))
            zone = _zone.id
        if zone is None:
            zone: int = request.session.get('zone')  # zone => Zone.pk
        if zone:
            _zones = Zones.objects.filter(pk=zone).values_list('partner_id', flat=True)
        else:
            _zones = Zones.objects.order_by('-is_default_zone').values_list('partner_id', flat=True)

        # sr_set = StockRecord.objects.filter(
        #     partner_id__in=_zones, num_in_stock__gt=0,
        #     product__in=queryset,
        #     product__parent_id__in=queryset.values_list('parent_id', flat=True)
        # ).values_list('product_id', flat=True)
        sr_set = StockRecord.objects.filter(Q(
            product__product_class_id=_pclass) | Q(product__parent__product_class_id=_pclass),
            partner_id__in=_zones, num_in_stock__gt=0).values_list('product_id', flat=True)

        child_selections = Q(Q(structure=Product.CHILD) & Q(parent_id__in=sr_set))
        parent_selections = Q(Q(structure=Product.STANDALONE) & Q(id__in=sr_set))
        qs = queryset.filter(parent_selections | child_selections)

        if _sort:
            _sort = [SORT_BY_MAP[key] for key in _sort.split(',') if key and key in SORT_BY_MAP.keys()]
            qs = apply_sort(queryset=qs, sort=_sort)

        # queryset = queryset.browsable().base_queryset()
        paginator = Paginator(qs, page_size)  # Show 18 contacts per page.
        empty_list = False
        try:
            page_number = paginator.validate_number(page_number)
        except PageNotAnInteger:
            page_number = 1
        except EmptyPage:
            page_number = paginator.num_pages
            empty_list = True
        page_obj = paginator.get_page(page_number)
        product_data = get_optimized_product_dict(qs=page_obj.object_list, request=request, ).values()
        from fuzzywuzzy import fuzz
        # product_data = get_optimized_product_dict_for_listing(qs=page_obj.object_list, request=request, ).values()
        # product_data = serializer_class(page_obj.object_list, many=True, context={'request': request}).data
        if _search:
            product_data = sorted(product_data,
                                  key=lambda p: fuzz.token_sort_ratio(_search.upper(), p['search_tags'].upper()),
                                  reverse=True)

        cat_data = {}
        if cat:
            cat_data['seo_title'] = cat.seo_title
            cat_data['seo_description'] = cat.seo_description
            cat_data['seo_keywords'] = cat.seo_keywords
            cat_data['ogimage'] = request.build_absolute_uri(cat.ogimage.url) if cat.ogimage else None

        return list_api_formatter(
            request, paginator=paginator, page_obj=page_obj,
            results=product_data, product_class=rc, title=title,
            bread_crumps=get_breadcrumb(_search, cat, product_range), seo_fields=cat_data)
    return Response(_inner())

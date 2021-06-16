import random
from collections import defaultdict
from typing import List, Dict, Any, Optional

from django.db.models import Sum, Q
from django.templatetags.static import static
from django.views.decorators.cache import cache_page
from rest_framework.decorators import api_view
from rest_framework.response import Response
from apps.api_set.serializers.mixins import ProductPrimaryImageFieldMixin, ProductPriceFieldMixinLite
from apps.api_set_v2.serializers.catalogue import CategorySerializer
from apps.api_set_v2.utils.product import get_optimized_product_dict
from apps.catalogue.models import Category, Product
from apps.dashboard.custom.models import HomePageMegaBanner, InAppBanner, OfferBanner
from apps.utils import banner_not_found
from lib.cache import cache_library


def get_home_content(request):
    pmg_mixin = ProductPrimaryImageFieldMixin()
    price_mixin = ProductPriceFieldMixinLite()
    pmg_mixin.context = price_mixin.context = {'request': request}
    categories = list(Category.get_root_nodes().exclude(slug="featured").only('id', 'name', 'slug', 'path').order_by(
        '-numchild'))
    random.shuffle(categories)
    categories = categories[:3]
    out = []
    cat_data = defaultdict(list)

    for cat in categories:
        cat_qs = Category.get_tree(cat)
        qs_filter = Q(categories__in=cat_qs) & Q(structure__in=[Product.STANDALONE, Product.PARENT])
        product_data = get_optimized_product_dict(request=request, qs_filter=qs_filter, limit=4, needs_stock=False)
        for parent_product, data in product_data.items():
            cat_data[cat].append(data)
    banners = list(InAppBanner.objects.all().filter(banner__isnull=False, product_range_id__isnull=False))

    def _(b):
        return {
            'title': b.title,
            'product_range': b.product_range_id,
            'banner': b.home_banner_wide_image(request),
        }

    slider_banner = [_(b) for b in banners if b.type == b.SLIDER_BANNER]
    full_screen_banner = [_(b) for b in banners if b.type == b.FULL_SCREEN_BANNER]
    segments = len(cat_data.keys())
    slider_length = len(slider_banner)
    if segments:
        segment_len = slider_length // segments
    else:
        segment_len = 1
    start, end = 0, segment_len
    for cat, data in cat_data.items():
        slides = slider_banner[start:end]
        random.shuffle(slides)
        slides = slides[:min(segment_len, 6)]
        start, end = start + segment_len, end + segment_len
        out.append({
            'name': cat.name,
            'slug': cat.slug,
            'products': data,
            'slider_banners': slides,
            'full_screen_banner': random.choice(full_screen_banner) if full_screen_banner else []
        })
    return out


@api_view(("GET",))
def index(request, *a, **k):
    cache_key = 'apps.api_set_v2.views.index?zone={}&v=0.0.3'.format

    def _inner():
        out = {'categories': []}
        cxt = {'context': {'request': request}}
        category_set = Category.get_root_nodes().exclude(slug="featured").annotate(c=Sum('product__basket_lines'))[:10]
        out['categories'] = CategorySerializer(category_set, **cxt, many=True).data

        out['offer_banners'] = [{
            'title': banner.title,
            'banner': banner.home_banner_wide_image(request) if banner.banner else banner_not_found(request),
            'product_range': banner.product_range_id
        } for banner in HomePageMegaBanner.objects.filter(product_range__isnull=False).order_by('-position')]
        out['content'] = get_home_content(request)
        return out

    # return Response(_inner())
    zone = request.session.get('zone')
    return Response(cache_library(cache_key(zone), cb=_inner, ttl=60 * 60 * 3))


def get_offer_content(request):
    pmg_mixin = ProductPrimaryImageFieldMixin()
    price_mixin = ProductPriceFieldMixinLite()
    pmg_mixin.context = price_mixin.context = {'request': request}
    offer_banners = InAppBanner.objects.all().filter(banner__isnull=False,
                                                     product_range_id__isnull=False).select_related('product_range')[:4]
    out = []
    off_data = defaultdict(list)

    for banner in offer_banners:
        qs = banner.product_range.all_products()
        product_data = get_optimized_product_dict(request=request, qs=qs, limit=4, )
        for parent_product, data in product_data.items():
            off_data[banner].append(data)
    for cat, data in off_data.items():
        out.append({
            'product_range': cat.id,
            'name': cat.title,
            'slug': cat.id,
            'products': data,
        })
    return out


OFFER_TOP_LABEL: str = 'top_wide_banners'
OFFER_MIDDLE_LABEL: str = 'middle_half_banners'
OFFER_BOTTOM_LABEL: str = 'bottom_wide_banners'
POS_01: str = 'position_01'
POS_02: str = 'position_02'


@api_view(("GET",))
def offers(request, *a, **k):
    banners = list(InAppBanner.objects.all().filter(banner__isnull=False, product_range_id__isnull=False))

    def _(b):
        return {'title': b.title, 'banner': b.home_banner_wide_image(request), 'product_range': b.product_range_id, }

    slider_banner = [_(b) for b in banners if b.type == b.SLIDER_BANNER]
    full_screen_banner = [_(b) for b in banners if b.type == b.FULL_SCREEN_BANNER]
    random.shuffle(full_screen_banner)
    random.shuffle(slider_banner)
    if len(full_screen_banner) < 4:
        full_screen_banner += full_screen_banner
    if len(slider_banner) < 2:
        slider_banner += slider_banner

    def get_as_dict(_index, lengthy_banner=True) -> List[Dict[str, Optional[Any]]]:
        nonlocal request, full_screen_banner, slider_banner
        banner_set = full_screen_banner if lengthy_banner else slider_banner
        if banner_set and _index < len(banner_set):
            return [banner_set[_index], ]
        else:
            return [{
                'title': 'Banner Not Set',
                'banner': request.build_absolute_uri(static('static/l6.jpg' if lengthy_banner else 'static/m4.jpg')),
                'product_range': 0
            }, ]

    _out = {
        OFFER_TOP_LABEL: {
            POS_01: get_as_dict(0),
            POS_02: get_as_dict(1)
        },
        OFFER_MIDDLE_LABEL: {
            POS_01: get_as_dict(0, False),
            POS_02: get_as_dict(1, False)
        },
        OFFER_BOTTOM_LABEL: {
            POS_01: get_as_dict(2),
            POS_02: get_as_dict(3),
        },
        'bottom_dataset': get_offer_content(request)
    }

    # arrays_config = (
    #     # (Array                               'default static image',   allow_many ),
    #     (out[OFFER_TOP_LABEL][POS_01],    'static/l6.jpg',         True),
    #     (out[OFFER_TOP_LABEL][POS_02],    'static/l6.jpg',         False),
    #     (out[OFFER_MIDDLE_LABEL][POS_01], 'static/m4.jpg',         False),
    #     (out[OFFER_MIDDLE_LABEL][POS_02], 'static/m4.jpg',         False),
    #     (out[OFFER_BOTTOM_LABEL][POS_01], 'static/l6.jpg',         False),
    #     (out[OFFER_BOTTOM_LABEL][POS_02], 'static/l6.jpg',         False),
    # )

    return Response(_out)

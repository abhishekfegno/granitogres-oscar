import random
import string
from collections import defaultdict
from typing import List, Dict, Any, Optional

from django.db.models import Sum, Q
from django.templatetags.static import static
from django.views.decorators.cache import cache_page
from oscar.apps.offer.models import Range
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.api_set.serializers.mixins import ProductPrimaryImageFieldMixin, ProductPriceFieldMixinLite
from apps.api_set_v2.serializers.catalogue import CategorySerializer
from apps.api_set_v2.utils.product import get_optimized_product_dict
from apps.availability.models import PinCode
from apps.catalogue.models import Category, Product
from apps.dashboard.custom.models import HomePageMegaBanner, InAppBanner, OfferBanner, TopCategory, OfferBox, \
    InAppFullScreenBanner, InAppSliderBanner, SocialMediaPost, SiteConfig
from apps.utils import banner_not_found
from lib.cache import cache_library


@api_view(['GET'])
def get_session_id(request):
    print(request.META['REMOTE_ADDR'])
    value = ''.join(random.choices(string.ascii_lowercase+string.digits, k=50))

    return Response({"session-id": value})


def get_home_content(request):
    pmg_mixin = ProductPrimaryImageFieldMixin()
    price_mixin = ProductPriceFieldMixinLite()
    pmg_mixin.context = price_mixin.context = {'request': request}
    categories = list(Category.get_root_nodes().exclude(slug="featured").only('id', 'name', 'slug', 'path').order_by(
        '-numchild'))
    random.shuffle(categories)
    categories = categories[:2]
    out = []
    cat_data = defaultdict(list)

    for cat in categories:
        cat_qs = Category.get_tree(cat)
        qs_filter = Q(categories__in=cat_qs) & Q(structure__in=[Product.STANDALONE, Product.PARENT])
        limit_per_cat = 4
        product_data = get_optimized_product_dict(request=request, qs_filter=qs_filter, limit=limit_per_cat*3, needs_stock=False)
        for parent_product, data in product_data.items():
            if len(cat_data[cat]) < limit_per_cat:
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
    cache_key = 'apps.api_set_v2.views.index?zone={}&v=0.0.9'.format

    """
        the _inner() method now has 5 slugs:
            exclusive-products,
            furnitures-for-your-home,
            jumbo-offer,
            offer-banner-x3,
            customer-favorites
        these slug is set on Range signal(post_save) and the cache is cleared accordingly.
        
        if there is a need to add more slug,add it below
            
    """
    def _inner():
        out = {'categories': []}
        cxt = {'context': {'request': request}}
        # category_set = Category.get_root_nodes().exclude(Q(exclude_in_listing=True)|Q(slug="featured")).annotate(c=Sum('product__basket_lines'))[:10]
        # out['categories'] = CategorySerializer(category_set, **cxt, many=True).data
        out['offer_banners'] = [{
            'title': banner.title,
            'banner': banner.home_banner_wide_image(request) if banner.banner else banner_not_found(request),
            'thumbnail': banner.home_banner_wide_image_thumbnail(request) if banner.banner else banner_not_found(request),
            'product_range': banner.product_range.slug
        } for banner in HomePageMegaBanner.objects.filter(product_range__isnull=False).order_by('-position')]
        # out['content'] = get_home_content(request)
        exclusive_products_slug = 'exclusive-products'
        exclusive_products, _created = Range.objects.get_or_create(
            slug=exclusive_products_slug,
            defaults={
                'name': 'Exclusive Products',
                'is_public': True,
            }
        )
        furniture_for_your_home_slug = 'furnitures-for-your-home'
        furniture_for_your_home, _created = Range.objects.get_or_create(
            slug=furniture_for_your_home_slug,
            defaults={
                'name': 'Furnitures for your home',
                'is_public': True,
            }
        )
        jambo_offer_slug = 'jumbo-offer'
        jambo_offer, _created = Range.objects.get_or_create(
            slug=jambo_offer_slug,
            defaults={
                'name': 'Jumbo Offers',
                'is_public': True,
            }
        )
        offer_banner_3_slug = 'offer-banner-x3'
        offer_banner_3, _created = Range.objects.get_or_create(
            slug=offer_banner_3_slug,
            defaults={
                'name': '',
                'is_public': True,
            }
        )
        picked_for_you_slug = 'picked-for-you'
        picked_for_you, _created = Range.objects.get_or_create(
            slug=picked_for_you_slug,
            defaults={
                'name': 'Picked for you',
                'is_public': True,
            }
        )
        customer_favorites_slug = 'customer-favorites'
        customer_favorites, _created = Range.objects.get_or_create(
            slug=customer_favorites_slug,
            defaults={
                'name': 'Customer Favorites',
                'is_public': True,
            }
        )
        pd = lambda *args, **kwargs: list(get_optimized_product_dict(*args, **kwargs).values())

        # def sorting_fun(item):
        #     if not item['price']['variants']:
        #         return item['price']['price']['net_stock_level']
        #     return sorted(item['price']['variants'], key=lambda variant: variant['price']['net_stock_level'], reverse=True)[0]['price']['net_stock_level']
        #
        # def pd(*args, **kwargs):
        #     data = list(sorted(get_optimized_product_dict(*args, **kwargs).values(), key=sorting_fun, reverse=True))
        #     return data

        out['content'] = [
            {
                'model': 'image_gallery_x6',
                'title': 'TOP CATEGORIES',
                'slug': 'top-category',
                'content': [tc.serialize(request) for tc in TopCategory.objects.all().select_related('product_range').order_by('-position')],
                'view_all': None,
                'bg': '#fff',
                'color': '#333',
            },
            {
                'model': 'slider',
                'id': exclusive_products.id,
                'title': exclusive_products.name,
                'slug': exclusive_products.slug,
                'content': pd(request, qs=exclusive_products.all_products(), limit=8, ),
                'view_all': exclusive_products.slug,
                'bg': '#f5f6fa',
                'color': '#555',
            },
            {
                'model': 'slider',
                'title': furniture_for_your_home.name,
                'slug': furniture_for_your_home.slug,
                'content': pd(request, qs=furniture_for_your_home.all_products(), limit=8, ),
                'view_all': exclusive_products.slug,
                'bg': '#f5f6fa',
                'color': '#555',
            },
            {
                'model': 'offer_boxes',
                'title': 'EXPLORE OUR LATEST COLLECTIONS',
                'slug': 'explore-our-latest-collections',
                'content': [tc.serialize(request) for tc in OfferBox.objects.all().order_by('-position')],
                'view_all': '/shop/',
                'bg': '#fff1da',
                'color': '#555555',
            },
            {
                'model': 'slider',
                'title': jambo_offer.name,
                'slug': jambo_offer.slug,
                'content': pd(request, qs=jambo_offer.all_products(), limit=8, ),
                'view_all': jambo_offer.slug,
                'bg': '#f5f6fa',
                'color': '#333',
            },
            {
                'model': 'image_gallery_x3',
                'title': '',
                'slug': offer_banner_3.slug,
                'content': [tc.serialize(request) for tc in InAppSliderBanner.objects.all().order_by('-position')],
                'view_all': None,
                'bg': '#fff',
                'color': '#333'
            },
            {
                'model': 'full_width_banner',
                'title': '',
                'slug': 'full_width_banner',
                'content': [ban.serialize(request) for ban in InAppFullScreenBanner.objects.all()],
                'view_all': None,
                'bg': '#fff',
                'color': '#333'
            },
            {
                'model': 'slider',
                'title': picked_for_you.name,
                'slug': picked_for_you.slug,
                'content': pd(request, qs=picked_for_you.all_products(), limit=8, ),
                'view_all': picked_for_you.slug,
                'bg': '#f5f6fa',
                'color': '#555',
            },
            {
                'model': 'slider',
                'title': customer_favorites.name,
                'slug': customer_favorites.slug,
                'content': pd(request, qs=customer_favorites.all_products(), limit=8, ),
                'view_all': customer_favorites.slug,
                'bg': '#f5f6fa',
                'color': '#555',
            },
            {
                'model': 'social_media_posts',
                'title': '#letyourhauzevolve',
                'slug': 'letyourhauzevolve',
                'content': [smp.serialize(request) for smp in SocialMediaPost.objects.all()],
                'view_all': None,
                'bg': '#f5f6fa',
                'color': '#555',
            },
        ]
        out['siteconfig'] = [field for field in SiteConfig.objects.all().values('home_seo_title', 'home_seo_description',
                                                                                'home_seo_keywords', 'home_seo_image',
                                                                                'home_seo_image_alt')]

        out['seo_footer'] = [field for field in SiteConfig.objects.all().values('home_seo_footer')]

        return out

    # return Response(_inner())
    user = request.user.username
    print(user)
    zone = request.session.get('zone')
    key = cache_key(zone)
    return Response(cache_library(cache_key(key), cb=_inner, ttl=60 * 60 * 24))


@api_view(("GET",))
def pincode_list(request, *a, **k):
    cache_key = 'apps.api_set_v2.views.pincode?v=0.0.5'

    def _inner():
        return {
            'pincodes': PinCode.objects.filter(
                depth=PinCode.POSTAL_CODE_DEPTH).values_list('name', 'code')
        }
    return Response(cache_library(cache_key, cb=_inner, ttl=60 * 60 * 24))


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

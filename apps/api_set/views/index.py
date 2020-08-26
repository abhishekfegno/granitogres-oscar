# /home/jk/code/grocery/apps/api_set/views/index.py
import random
from collections import defaultdict, OrderedDict

from allauth.account.models import EmailAddress
from django.conf import settings
from django.core.paginator import Paginator
from django.db import models
from django.db.models import Count
from django.template.defaulttags import regroup
from django.templatetags.static import static
from django.utils.timezone import now
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
from oscar.apps.offer.models import ConditionalOffer, Range
from oscar.core.loading import get_model
from oscarapi.utils.loading import get_api_class, get_api_classes
from rest_framework.decorators import api_view
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from sorl.thumbnail import get_thumbnail

from apps.api_set.serializers.catalogue import (
    CategorySerializer, Category, Product,
    ProductListSerializer, SimpleOfferBannerSerializer
)
from apps.basket.models import Basket
from apps.catalogue.models import ProductImage
from apps.dashboard.custom.models import OfferBanner
from apps.utils.urls import list_api_formatter
from lib.cache import get_featured_path

BasketSerializer = get_api_class("serializers.basket", "BasketSerializer")
Order = get_model('order', 'Order')
BasketLine = get_model('basket', 'Line')


@api_view(("GET",))
def home(request, *a, **k):
    user = None
    basket = None
    b_count = 0
    if request.user.is_authenticated:
        user_fields = ['id', 'mobile', 'email', 'first_name', 'last_name', 'is_active',
                       'status', 'is_delivery_request_pending']
        user = {field: getattr(request.user, field) for field in user_fields}
        basket = Basket.open.filter(owner=request.user).last()
    if basket is None:
        basket = request.basket or None
    b_count = basket.num_lines if basket else 0

    return Response({
        "user": user,
        "cart_item_count": b_count,
    })


@api_view(("GET",))
@cache_page(60 * 60 * 2)
def index(request, *a, **k):
    index = 0
    out = {'home': []}
    cxt = {'context': {'request': request}}
    category_set = Category.objects.filter(
        depth__in=[2, 3]
    ).annotate(c=Count('product__basket_lines')).order_by('depth', 'c')[:10]
    categories = CategorySerializer(category_set, **cxt, many=True).data

    for slot in range(1, 3):
        out['home'].append({
            'top': categories[index:index + 3],
            'middle': [{
                'banner': request.build_absolute_uri(ob.banner.url),
                'product_range': ob.product_range_id
            } for ob in OfferBanner.objects.filter(**{'display_area': OfferBanner.HOME_PAGE,
                                                      'position': slot}).order_by('-id')],
            'bottom': categories[index + 3:index + 5],
        })
        index += 5

    return Response(out)


OFFER_TOP_LABEL: str = 'top_wide_banners'
OFFER_MIDDLE_LABEL: str = 'middle_half_banners'
OFFER_BOTTOM_LABEL: str = 'bottom_wide_banners'
POS_01: str = 'position_01'
POS_02: str = 'position_02'


@api_view(("GET",))
# @cache_page(60 * 60 * 2)
def offers(request, *a, **k):
    offer_banner = OfferBanner.objects.all().exclude(
        display_area=OfferBanner.HOME_PAGE
    ).order_by('position')                      #.values('display_area', 'position', 'banner', 'product_range')
    _out = {OFFER_TOP_LABEL: [], OFFER_MIDDLE_LABEL: [], OFFER_BOTTOM_LABEL: []}
    for item in offer_banner:
        _out[{
            OfferBanner.OFFER_TOP: OFFER_TOP_LABEL,
            OfferBanner.OFFER_MIDDLE: OFFER_MIDDLE_LABEL,
            OfferBanner.OFFER_BOTTOM: OFFER_BOTTOM_LABEL,
        }[item.display_area]].append(item)

    out = defaultdict(dict)
    for key, value_list in _out.items():
        out[key][POS_01] = []
        out[key][POS_02] = []
        for banners in value_list:
            slot = [POS_01, POS_02][banners.position-1]
            out[key][slot].append({
                'banner': banners.mobile_wide_image(request),
                'product_range': banners.product_range_id
            })

    arrays_config = (
        # (Array                               'default static image',   allow_many ),
        (out[OFFER_TOP_LABEL][POS_01],    'static/l6.jpg',         True),
        (out[OFFER_TOP_LABEL][POS_02],    'static/l6.jpg',         False),
        (out[OFFER_MIDDLE_LABEL][POS_01], 'static/m4.jpg',         False),
        (out[OFFER_MIDDLE_LABEL][POS_02], 'static/m4.jpg',         False),
        (out[OFFER_BOTTOM_LABEL][POS_01], 'static/l6.jpg',         False),
        (out[OFFER_BOTTOM_LABEL][POS_02], 'static/l6.jpg',         False),
    )

    for array, img, allow_many in arrays_config:
        if len(array) == 0:
            array.append({'banner': request.build_absolute_uri(static(img)), 'product_range': None})
        if allow_many is False:
            del array[1:]    # only one is allowed in banner.
    return Response(out)


@api_view(("GET",))
def offer_products(request, *a, **k):
    cxt = {'context': {'request': request}}
    serializer_class = ProductListSerializer
    page_number = request.GET.get('page', 1)
    page_size = request.GET.get('page_size', settings.DEFAULT_PAGE_SIZE)

    obj = get_object_or_404(OfferBanner, code=k.get('slug'), offer__status=ConditionalOffer.OPEN)
    queryset = obj.products().filter(
        structure__in=['standalone', 'child'], is_public=True, stockrecords__isnull=False
    ).distinct('id').order('-id')
    paginator = Paginator(queryset, page_size)  # Show 18 contacts per page.
    page_obj = paginator.get_page(page_number)
    product_data = serializer_class(page_obj.object_list, many=True, context={'request': request}).data
    return Response(list_api_formatter(request, page_obj=page_obj, results=product_data))

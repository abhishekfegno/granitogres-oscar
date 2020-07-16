# /home/jk/code/grocery/apps/api_set/views/index.py
import random
from collections import defaultdict, OrderedDict

from allauth.account.models import EmailAddress
from django.conf import settings
from django.core.paginator import Paginator
from django.db import models
from django.db.models import Count
from django.template.defaulttags import regroup
from django.utils.timezone import now
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
    b_count = 0
    if request.user.is_authenticated:
        user_fields = ['id', 'mobile', 'email', 'first_name', 'last_name', 'is_active', ]
        user = {field: getattr(request.user, field) for field in user_fields}
        b_count = Basket.open.filter(owner=request.user).last().num_lines
    else:
        b_count = request.basket.num_lines
    return Response({
        "user": user,
        "cart_item_count": b_count,
    })


@api_view(("GET",))
def index(request, *a, **k):
    index = 0
    out = {'home': []}
    cxt = {'context': {'request': request}}
    category_set = Category.objects.filter(
        depth__in=[2, 3]
    ).annotate(c=Count('product__basket_lines')).order_by('depth', 'c')[:10]
    categories = CategorySerializer(category_set, **cxt, many=True).data

    for slot in range(2):
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


@api_view(("GET",))
def offers(request, *a, **k):
    offer_banner = OfferBanner.objects.all().exclude(
        display_area=OfferBanner.HOME_PAGE
    ).order_by('position') #.values('display_area', 'position', 'banner', 'product_range')
    out = defaultdict(list)
    for item in offer_banner:
        out[{
            OfferBanner.OFFER_TOP: 'top_wide_banners',
            OfferBanner.OFFER_MIDDLE: 'middle_half_banners',
            OfferBanner.OFFER_BOTTOM: 'bottom_wide_banners',
        }[item.display_area]].append(item)

    for key, value_list in out.items():
        out[key] = defaultdict(OrderedDict)
        for banners in value_list:
            pos = ['position_01', 'position_02'][banners.position-1]
            if pos not in out[key].keys():
                out[key][pos] = []
            out[key][pos].append({
                'banner': banners.mobile_wide_image(request),
                'product_range': banners.product_range_id
            })
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

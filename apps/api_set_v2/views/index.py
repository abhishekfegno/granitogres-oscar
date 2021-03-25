from collections import defaultdict

from django.db.models import Sum, Case, When, Value, F, CharField, Q
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.api_set.serializers.mixins import ProductPrimaryImageFieldMixin, ProductPriceFieldMixinLite
from apps.api_set_v2.serializers.catalogue import CategorySerializer, ProductSimpleListSerializer
from apps.api_set_v2.utils.product import get_optimized_product_dict
from apps.catalogue.models import Category, Product
from apps.dashboard.custom.models import HomePageMegaBanner
from apps.partner.models import StockRecord
from lib.cache import cache_library


def get_home_content(request):
    pmg_mixin = ProductPrimaryImageFieldMixin()
    price_mixin = ProductPriceFieldMixinLite()
    pmg_mixin.context = price_mixin.context = {'request': request}
    categories = Category.get_root_nodes().exclude(slug="featured").only('id', 'name', 'slug', 'path')
    out = []
    cat_data = defaultdict(list)
    for cat in categories:
        product_data = get_optimized_product_dict(
            request=request,
            qs_filter=Q(categories__in=Category.get_tree(cat)),
            limit=4,
        )
        for parent_product, data in product_data.items():
            cat_data[cat].append(data)
    for cat, data in cat_data.items():
        out.append({
            'name': cat.name,
            'slug': cat.slug,
            'products': data,
        })
    return out


@api_view(("GET",))
def index(request, *a, **k):
    cache_key = 'apps.api_set_v2.views.index?zone={}&v=1.0.1'.format

    def _inner():
        out = {'categories': []}
        cxt = {'context': {'request': request}}
        category_set = Category.objects.filter(
            depth__in=[2, 3]
        ).annotate(c=Sum('product__basket_lines')).order_by('depth', 'c')[:10]
        out['categories'] = CategorySerializer(category_set, **cxt, many=True).data

        out['offer_banners'] = [{
            'banner': banner.home_banner_wide_image(request),
            'product_range': banner.product_range_id
        } for banner in HomePageMegaBanner.objects.filter(product_range__isnull=False).order_by('-position')]

        out['content'] = get_home_content(request)
        return out
    zone = request.session.get('zone')
    return Response(cache_library(cache_key(zone), cb=_inner, ttl=60*60*3))

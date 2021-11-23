from django.conf import settings
from django.db.models import Count, Sum, Q, Case, When, Value, F, ForeignKey, SET_NULL, PositiveIntegerField, Prefetch
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
from factory.django import get_model
from oscar.core.loading import get_class
from rest_framework.decorators import api_view
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from apps.api_set.serializers.catalogue import (
    CategorySerializer, ProductDetailWebSerializer, custom_ProductListSerializer, ProductAttributeValue
)
from apps.api_set.views.orders import _login_required
from apps.api_set_v2.utils.filters import price_min_max_to_options
from apps.order.models import Line

from lib.product_utils import apply_search, recommended_class, ClassRecommendation
from apps.catalogue.models import Product, ProductAttribute, AttributeOption

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
    if request.session.get('location'):
        out = {
            'message': None,
            'status': True,
            'data': {
                'location': {
                    "zone_id": request.session.get('zone'),
                    "zone_name": request.session.get('zone_name'),
                    "location_id": request.session.get('location'),
                    "location_name": request.session.get('location_name')
                }
            }
        }
    else:
        out = {
            'message': 'Current Location is not provided.',
            'status': False
        }

    return Response({
        'results': serializer_class(instance=focused_product, context={'request': request, 'product': product}).data,
        'deliverable': out
    })


def __(val):
    if type(val.value) == AttributeOption:
        return str(val.value)
        # return {str(x) for x in val.options.all().values_list('name', flat=True)}
    else:
        return val.value


# def to_client_dict(value_array):
#     return [{
#         'label': value.vaue,
#         'pcount': value.product_count,
#         'is_checked': False
#     } for value in value_array]


def to_client_dict(value_array):
    return [{
        'label': value[0],
        'count': value[1],
        'is_checked': False
    } for value in value_array]


@api_view()
def filter_options(request, pk):
    attrs = ProductAttribute.objects.filter(is_visible_in_filter=True, product_class_id=pk).prefetch_related(Prefetch(
        'productattributevalue_set',
        queryset=ProductAttributeValue.objects.filter(product_count__gt=0))
    )
    out = []
    for attr in attrs:
        _inner_out = {}
        for value in attr.productattributevalue_set.filter(
                product_count__gt=0,
        ).order_by('-product_count'):
            if value.value not in _inner_out:
                _inner_out[value.value] = 0
            _inner_out[value.value] += value.product_count
        _inner_out = list(_inner_out.items())
        _inner_out.sort(key=lambda c: c[1], reverse=True)
        val = {
            'code': attr.code,
            'label': attr.name,
            'val': to_client_dict(_inner_out)
        }

        # values = attr.productattributevalue_set.exclude(value_text=None, product_count=0).order_by('value_text').distinct('value_text').values_list('value_text')

        out.append(val)
    rec_out = ClassRecommendation().get_max_min(pclass=pk)
    options = price_min_max_to_options(**rec_out)
    return Response({
        'results': out,
        'price_range': {
            'input_type': "select",
            "options": {
                "min_price": 0.0,
                "max_price": 0.0,
            }
        },
        "exclude_out_of_stock": True,
    })


def _sanitize(name):
    return " ".join([s.capitalize() for s in name.split(' ') if s.isalpha() and len(s) > 2])


@api_view()
def product_suggestions(request, **kwargs):
    _search = request.GET.get('q')
    _max_size = 10

    def _inner():
        out = {'results': [], 'class': None, }
        queryset = Product.objects.filter(is_public=True).filter(structure__in=(Product.STANDALONE, Product.PARENT))
        if _search:
            if _search:
                if len(_search) <= 2:
                    mode = '_simple'
                else:
                    mode = '_trigram'
                queryset = apply_search(queryset=queryset, search=_search, mode=mode)
            rc = recommended_class(queryset, search=_search)
            queryset = queryset.values('id', 'title', 'slug', 'product_class_id', )[:_max_size*3]
            _mapper = {}
            _mapper_len = 1
            for item in queryset:
                if item['title'] not in _mapper:
                    # title = item['title']
                    item['title'] = _sanitize(item['title'])
                    _mapper[item['title']] = item
                    _mapper_len += 1
                if _mapper_len > _max_size:
                    break
            out['results'] = list(_mapper.values())
            out['class'] = rc
        return out
    # c_key = cache_key.product_suggestion__key.format(_search)
    # out = cache_library(c_key, cb=_inner, ttl=180)
    return Response(_inner())


def get_products(_filter=None, _exclude=None, max_count=30):

    recommended_product_ids = Line.objects
    if _filter:
        recommended_product_ids = recommended_product_ids.filter(_filter)
    if _exclude:
        recommended_product_ids = recommended_product_ids.exclude(_exclude)
    recommended_product_ids = recommended_product_ids.annotate(usable_product_id=Case(
        When(product__structure='child',
             then=F('product__parent_id')),
        default=F('product_id'),
        output_field=PositiveIntegerField()
    )).values('usable_product_id').annotate(
        rank=Sum('quantity'),
    ).filter(rank__gte=2).order_by('-rank')[:max_count]
    recommended_product_dict = {f['usable_product_id']: f['rank'] for f in recommended_product_ids}
    recommended_products = Product.browsable.browsable().filter(id__in=recommended_product_dict.keys())
    recommended_products__ordered = sorted(recommended_products,
                                           key=lambda item: recommended_product_dict[item.pk], reverse=True)
    return recommended_products__ordered


@api_view()
@_login_required
# @cache_page(60*60*24)
# @vary_on_cookie
def budget_bag(request, **kwargs):
    user = request.user
    recommended_products = get_products(_filter=Q(order__user=user))
    most_selling_products = []
    if len(recommended_products) <= 12:
        most_selling_products = get_products(
            _exclude=Q(product__in=recommended_products, product__parent__in=recommended_products),
            max_count=15)
    out = {
        'recommended': custom_ProductListSerializer(recommended_products, context={'request': request}).data,
        'most_selling': custom_ProductListSerializer(most_selling_products, context={'request': request}).data,
    }
    return Response(out)





















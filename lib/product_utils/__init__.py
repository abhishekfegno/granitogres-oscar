from django.conf import settings
from django.db.models import Q, F, Count, Max, Min, Case, When, CharField
from oscar.core.loading import get_model
from rest_framework.generics import get_object_or_404

from apps.catalogue.models import Category, Product
from django.contrib.postgres.search import SearchQuery, SearchVector, SearchRank
from django.contrib.postgres.search import TrigramSimilarity

from lib.product_utils.search import _trigram_search, _simple_search, _similarity_with_rank_search, _similarity_search

ProductClass = get_model('catalogue', 'ProductClass')


def category_filter(queryset, category_slug, return_as_tuple=False):
    cat = get_object_or_404(Category, slug=category_slug)
    out = [queryset.filter(
        productcategory__category__in=Category.objects.filter(path__startswith=cat.path)), cat]
    return out if return_as_tuple else out[0]


def brand_filter(queryset, brand_ids):
    return queryset.filter(brand__in=brand_ids)


def apply_filter(queryset, _filter, null_value_compatability='__'):
    """
    _filter:
         input = weight:25,30,35::minprice:25::maxprice:45::available_only:1::color=Red,Black,Blue::ram:4 GB,8 GB
         _flt = [
             weight__in : [25, 30, 35],
             minprice : 25,
             maxprice : 45,
             available_only : 1
             color: [Red,Black,Blue]
             ram:[4 GB,8 GB]
         ]
    """
    filter_values_set = _filter.split('::')
    filter_params = {}

    def set_key(key, value):
        return k + '__in' if ',' in v else k

    def set_value(key, value):
        return [_v.strip() for _v in v.split(',')] if ',' in v else v.strip()

    for filter_values in filter_values_set:
        if ':' in filter_values and not filter_values.endswith(f':{null_value_compatability}'):
            k, v = filter_values.split(':', 1)

            # managed already
            # if v and v == null_value_compatability:
            #     continue  # frontend comfortability : frontend generated null value
            filter_params[set_key(k, v)] = set_value(k, v)

    price_from = price_to = None

    if 'minprice' in filter_params.keys() and filter_params['minprice'] == null_value_compatability:
        price_from = filter_params.pop('minprice')

    if 'maxprice' in filter_params.keys() and filter_params['maxprice'] == null_value_compatability:
        price_to = filter_params.pop('maxprice')

    exclude_out_of_stock = filter_params.pop('available_only') if 'available_only' in filter_params else None

    if price_from and price_to:
        price_from, price_to = min(price_from, price_to), max(price_from, price_to),
        queryset = queryset.filter(effective_price__range=(price_from, price_to))
    elif price_from:
        queryset = queryset.filter(effective_price__gte=price_from)

    elif price_to:
        queryset = queryset.filter(effective_price__lte=price_to)

    if exclude_out_of_stock:
        queryset = queryset.filter(effective_price__isnull=False)

    if exclude_out_of_stock:
        queryset = queryset.filter(effective_price__isnull=False)

    queryset = queryset.filter_by_attributes(**filter_params)
    return queryset


def apply_search(queryset, search: str, mode: str = '_similarity_with_rank_search', extends: bool = True):
    """
    search : string
    mode : selector_functions
            * _trigram              * _simple
            * _similarity_rank      * _similarity
    extends : Want Unmatched products if not match found?
    """

    if mode == '_trigram':  # default
        filter_func = _trigram_search
    elif mode == '_simple':
        filter_func = _simple_search
    elif mode == '_similarity_rank':
        filter_func = _similarity_with_rank_search
    elif mode == '_similarity':
        filter_func = _similarity_search
    else:
        raise Exception('Invalid Search Mode')
    return filter_func(queryset, search, extends=extends)


def apply_sort(queryset, sort=None):
    if sort is not None:
        return queryset.order_by(*sort)
    return queryset


def recommended_class(queryset):
    # Computation in python. Query optimization verified! average of 5-18 iterations and 8 query hits
    values = queryset.values('id', 'product_class', 'parent__product_class')
    struct = {}
    max_id = None
    max_count = 0
    for item in values:
        key = item['product_class'] or item['parent__product_class']
        if key not in struct.keys():
            struct[key] = 1
        else:
            struct[key] += 1
        if max_count <= struct[key]:
            max_id = key
            max_count = struct[key]
    if len(values) and max_count * 1.0 > len(values) * 3 / 4 or settings.DEBUG:  # at least 3/4th are of same class.
        return {
            'id': max_id,
            **Product.objects.filter(effective_price__isnull=False, product_class_id=max_id).aggregate(
                max_price=Max('effective_price'),
                min_price=Min('effective_price'),
            )
        }

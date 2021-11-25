import json
import logging
import pdb

from django.conf import settings
from django.db.models import Q, F, Count, Max, Min, Case, When, CharField
from oscar.core.loading import get_model
from rest_framework.generics import get_object_or_404

from apps.catalogue.models import Category, Product
from django.contrib.postgres.search import SearchQuery, SearchVector, SearchRank
from django.contrib.postgres.search import TrigramSimilarity

from apps.partner.models import StockRecord
from lib.product_utils.search import _trigram_search, _simple_search, _similarity_with_rank_search, _similarity_search

ProductClass = get_model('catalogue', 'ProductClass')


def category_filter(queryset, category_slug, return_as_tuple=False):
    cat = get_object_or_404(Category, slug=category_slug)
    out = [queryset.filter(
        productcategory__category__in=Category.objects.filter(path__startswith=cat.path)), cat]
    return out if return_as_tuple else out[0]


def brand_filter(queryset, brand_ids):
    return queryset.filter(brand__in=brand_ids)


def apply_filter(queryset, _filter, null_value_compatability='__', product_class=None):
    """
    _filter:
         input = weight:25|30|35::minprice:25::maxprice:45::available_only:1::color=Red|Black|Blue::ram:4 GB|8 GB
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
    client_side_value_splitter = "|"

    def set_key(key, value):
        return k + '__in' if client_side_value_splitter in v else k

    def set_value(key, value):
        return [_v.strip() for _v in v.split(client_side_value_splitter)] if client_side_value_splitter in v else v.strip()

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
    print(f"Applying Filter!   => {_filter} => {queryset.count()}")
    valid_attributes = set(filter_params.keys()).intersection(set(product_class.attributes.values_list('code', flat=True)))
    print(f"VALID ATTRIBUTES!  {valid_attributes}")
    kwargs = {key: val for key, val in filter_params.items() if key in valid_attributes}
    print(f"VALID Kwargs!  {json.dumps(kwargs)}")
    queryset = queryset.filter_by_attributes(**kwargs)
    print(f"QS COUNT!  {queryset.count()}")
    return queryset


def apply_search(queryset, search: str, mode: str = '_trigram', extends: bool = True):
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


class ClassRecommendation(object):

    def get_max_min(self, pclass=None):
        qs = StockRecord.objects.exclude(product__structure=Product.PARENT).filter(
            price_excl_tax__gt=0)
        if pclass:
            qs = qs.filter(product__product_class_id=pclass)
        return qs.aggregate(
            max_price=Max('price_excl_tax'),
            min_price=Min('price_excl_tax'),
        )

    def render(self, _id,  display_classes=False):
        if display_classes:
            product_classes = ProductClass.objects.all().values('id', 'name')
        else:
            product_classes = []
        return {
            'id': _id,
            **self.get_max_min(_id),
            'product_classes': product_classes
        }

    def recommend(self, **kwargs):
        recommended_pclass = None   # to fill if in case of any secondary priority
        if 'pclass' in kwargs and kwargs['pclass']:
            return self.render(kwargs['pclass'])
        if 'search' in kwargs and kwargs['search']:
            pass
        if 'range' in kwargs and kwargs['range']:
            _pclass = kwargs['range'].classes.all().first()
            if _pclass:
                return self.render(_pclass.id)
        if 'category' in kwargs and kwargs['category'] and kwargs['category'] and kwargs['category'].product_class_id:
            return self.render(kwargs['category'].product_class_id)
        if 'queryset' in kwargs:
            return self.render(_id=None, display_classes=True)
            # values = kwargs['queryset'].values('id', 'product_class', 'parent__product_class')
            # struct = {}
            # max_id = None
            # max_count = 0
            # for item in values:
            #     key = item['product_class'] or item['parent__product_class']
            #     if key not in struct.keys():
            #         struct[key] = 1
            #     else:
            #         struct[key] += 1
            #     if max_count <= struct[key]:
            #         max_id = key
            #         max_count = struct[key]
            # if len(values) and max_count * 2.0 > len(values) or settings.DEBUG:  # at least 3/4th are of same class.
            #     return self.render(max_id)

        return self.render(_id=None, display_classes=True)


def recommended_class(queryset, **kwargs):

    # Computation in python. Query optimization verified! average of 5-18 iterations and 8 query hits
    params = {
        'search': kwargs.get('search'),
        'range': kwargs.get('range'),
        'category': kwargs.get("category"),
        'pclass': kwargs.get('pclass'),
        'queryset': queryset
    }
    return ClassRecommendation().recommend(**params)







from django.conf import settings
from haystack.query import SearchQuerySet
from oscar.apps.search.forms import BrowseCategoryForm
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.api_set.search import GrocerySearchHandler
from apps.api_set.serializers.catalogue import (custom_ProductListSerializer)
from apps.catalogue.models import Product
from apps.utils.urls import list_api_formatter


@api_view()
def product_list(request, category='all', **kwargs):
    """
    PRODUCT LISTING API, (powering,  list /c/all/, /c/<category_slug>/,  )
    q = "A search term "
    product_range = '<product-range-id>'
    sort = <depricated>
    filter = <depricated>
    """

    queryset = Product.browsable.browsable().base_queryset()
    serializer_class = custom_ProductListSerializer
    _search = request.GET.get('q')
    _sort = request.GET.get('sort')
    _product_range = request.GET.get('product_range')
    page_number = int(str(request.GET.get('page', 1)))
    page_size = int(str(request.GET.get('page_size', settings.DEFAULT_PAGE_SIZE)))
    search_form_class = BrowseCategoryForm
    out = {
        'query': None,
        'suggestion': None,
        'count': 0,
    }
    #
    # if _product_range:
    #     _product_range_object = get_object_or_404(Range, id=_product_range)
    #     queryset = _product_range_object.all_products().base_queryset()
    #
    # if category != 'all':
    #     queryset, cat = category_filter(queryset=queryset, category_slug=category)

    # if _search:
    handler = GrocerySearchHandler(request.GET, request.get_full_path(), form_class=search_form_class,
                                   paginate_by=page_size)
    out['query'] = handler.search_form.cleaned_data['q']
    out['suggestion'] = handler.search_form.get_suggestion()
    out['count'] = handler.results.facet_counts()

    def _inner():
        nonlocal handler, queryset, out
        page_obj = handler.paginator.get_page(page_number)
        product_data = serializer_class(page_obj.object_list, context={'request': request}).data
        return list_api_formatter(
            request, page_obj=page_obj,
            results=product_data,
            # product_class=rc,
            **out)

    return Response(_inner())


@api_view()
def query_product_suggestions(request, **kwargs):
    _search = request.GET.get('q')
    _max_size = 10
    out = {'results': [],   'class': None, }

    sqs = SearchQuerySet().autocomplete(title=_search)[:_max_size]
    for result in sqs:
        out['results'].append({
            'title': result.title,
            'slug': result.slug
        })

    # return JsonResponse(out, status=(400 if len(out['results']) == 0 else 200))
    return Response(out, status=(400 if len(out['results']) == 0 else 200))



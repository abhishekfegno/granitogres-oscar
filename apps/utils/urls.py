from collections import OrderedDict

from django.db.models import QuerySet


def generate_path(request, **kwargs):
    path = request._request.path_info
    b = request.build_absolute_uri
    return b("{}?{}".format(
        path,
        "&".join(
            [f"{k}={kwargs.get(k)}" for k in kwargs.keys() if kwargs.get(k)]
        )
    ))


def list_api_formatter(request, paginator, page_obj, results=None, **kwargs):
    next_url = prev_url = None
    if results is None:
        results = page_obj.object_list
    params = {k: request.GET.get(k) for k, v in request.GET.items()}
    if page_obj.has_next():
        params['page'] = page_obj.next_page_number()
        next_url = generate_path(request, **params)

    if page_obj.has_previous():
        params['page'] = page_obj.previous_page_number()
        prev_url = generate_path(request, **params)
    # out = paginator.get_paginated_response_context(results)
    count = len(results)
    return OrderedDict([
        ('count', paginator.count),
        ('num_pages', paginator.num_pages),
        ('next_url', next_url),
        ('prev_url', prev_url),
        ('results', results),
        *kwargs.items()
    ])


def dummy_list_api_formatter():
    return {
        'count': 0,
        'next_url': None,
        'prev_url': None,
        'results': [],
    }

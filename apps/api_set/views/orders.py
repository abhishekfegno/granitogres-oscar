from django.conf import settings
from django.core.paginator import Paginator
from oscar.core.loading import get_model
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from apps.api_set.serializers.orders import OrderListSerializer, OrderDetailSerializer, OrderMoreDetailSerializer
from apps.utils.urls import list_api_formatter

Order = get_model('order', 'Order')


def _login_required(func):
    def _wrapper(request, *args, **kwargs):
        if request.user.is_anonymous:
            return Response({'detail': 'Authentication Required@'}, status=status.HTTP_400_BAD_REQUEST)
        return func(request, *args, **kwargs)
    _wrapper.__name__ = func.__name__
    _wrapper.__doc__ = func.__doc__
    return _wrapper


@api_view(("GET",))
@_login_required
def orders(request, *a, **k):
    cxt = {'context': {'request': request}}
    # if request.user.is_anonymous:
    #     return Response({'detail': 'Authentication Required@'}, status=status.HTTP_400_BAD_REQUEST)
    serializer_class = OrderListSerializer
    page_number = request.GET.get('page', 1)
    page_size = request.GET.get('page_size', settings.DEFAULT_PAGE_SIZE)
    queryset = Order.objects.filter(user=request.user)
    paginator = Paginator(queryset, page_size)  # Show 18 contacts per page.
    page_obj = paginator.get_page(page_number)
    product_data = serializer_class(page_obj.object_list, many=True, context={'request': request}).data
    return Response(list_api_formatter(request, page_obj=page_obj, results=product_data))


@api_view(("GET",))
@_login_required
def orders_detail(request, *a, **k):
    _object = get_object_or_404(Order.objects.filter(user=request.user), pk=k.get('pk'))
    serializer_class = OrderDetailSerializer
    return Response(serializer_class(_object, context={'request': request}).data)


@api_view(("GET",))
@_login_required
def orders_more_detail(request, *a, **k):
    _object = get_object_or_404(Order.objects.filter(user=request.user), pk=k.get('pk'))
    serializer_class = OrderMoreDetailSerializer
    return Response(serializer_class(_object, context={'request': request}).data)





from django.conf import settings
from django.core.paginator import Paginator
from rest_framework.decorators import api_view
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from apps.api_set_v2.serializers.orders import OrderListSerializer
from apps.api_set.views.orders import _login_required   # noqa: underscored import
from apps.order.models import Order
from apps.utils.urls import list_api_formatter
from apps.api_set.views.orders import orders_detail     # noqa: using in v2 urls


@api_view(("GET",))
@_login_required
def orders(request, *a, **k):
    cxt = {'context': {'request': request}}
    serializer_class = OrderListSerializer
    page_number = request.GET.get('page', 1)
    page_size = request.GET.get('page_size', settings.DEFAULT_PAGE_SIZE)
    queryset = Order.objects.filter(user=request.user).prefetch_related(
        'lines',        # calculate any cancelled or cancelling order lines
                        # cutting down 60% of queries
    ).order_by('-id')
    paginator = Paginator(queryset, page_size)  # Show 18 contacts per page.
    page_obj = paginator.get_page(page_number)
    product_data = serializer_class(page_obj.object_list, many=True, context={'request': request}).data
    return Response(list_api_formatter(request, page_obj=page_obj, results=product_data))



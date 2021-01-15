from django.conf import settings
from django.core.paginator import Paginator
from oscar.core.loading import get_model
from oscarapicheckout.serializers import OrderSerializer
from rest_framework import status, serializers
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from apps.api_set.serializers.basket import WncBasketSerializer
from apps.api_set.serializers.orders import OrderListSerializer, OrderDetailSerializer, OrderMoreDetailSerializer
from apps.order.processing import EventHandler
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


@api_view(("POST",))
@_login_required
def order_line_return_request(request, *a, **k):
    """
    POST {
        "line_ids": [15, 26, 14],
        "reason": "some reason"
    }

    """

    #  Validations
    errors = {
        "errors": {}
    }

    if type(request.data.get('line_ids', None)) is not list:
        errors['errors']['line_ids'] = "Required"
    if not request.data.get('reason', None):
        errors['errors']['reasons'] = "Required"
    if len(errors['errors'].keys()):
        return Response(errors, status=400)

    # Body
    _order = get_object_or_404(Order.objects.filter(user=request.user), pk=k.get('pk'))
    order_lines = _order.lines.all().filter(id__in=request.data.get('line_ids'))
    handler = EventHandler()
    try:
        if order_lines:
            for line in order_lines:
                handler.handle_order_line_status_change(line, settings.ORDER_STATUS_RETURN_REQUESTED,
                                                        note_type="User")
                order = line.order
                for reason in request.data.get('reason', []):
                    handler.create_note(order, message=reason, note_type="User")

        else:
            raise Exception(f"No Line(s)  Found against Order {_order.number}: Lines {request.data.get('line_ids')}")
    except Exception as e:
        errors['errors']['non_field_errors'] = str(e)
        return Response(errors, status=400)
    else:
        return Response(OrderDetailSerializer(_order, context={'request': request}).data, status=200)





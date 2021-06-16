from django.conf import settings
from django.core.paginator import Paginator
from oscar.apps.payment.exceptions import PaymentError
from oscar.core.loading import get_model
from oscarapicheckout.serializers import OrderSerializer
from rest_framework import status, serializers
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from apps.api_set.serializers.basket import WncBasketSerializer
from apps.api_set.serializers.orders import OrderListSerializer, OrderDetailSerializer, OrderMoreDetailSerializer
from apps.order.models import Order
from apps.order.processing import EventHandler
from apps.utils.urls import list_api_formatter
from oscar.apps.order import exceptions as order_exceptions

from apps.utils.utils import get_statuses


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
    queryset = Order.objects.filter(user=request.user).prefetch_related(
        'lines', 'lines__product',
        'lines__product__images').select_related('shipping_address')
    paginator = Paginator(queryset, page_size)  # Show 18 contacts per page.
    page_obj = paginator.get_page(page_number)
    product_data = serializer_class(page_obj.object_list, many=True, context={'request': request}).data
    return Response(list_api_formatter(request, page_obj=page_obj, results=product_data))


@api_view(("GET",))
@_login_required
def orders_v2(request, *a, **k):
    cxt = {'context': {'request': request}}
    serializer_class = OrderListSerializer
    page_number = request.GET.get('page', 1)
    page_size = request.GET.get('page_size', settings.DEFAULT_PAGE_SIZE)
    queryset = Order.objects.filter(user=request.user).prefetch_related('lines', 'lines__product', 'lines__product__images')
    paginator = Paginator(queryset, page_size)  # Show 18 contacts per page.
    page_obj = paginator.get_page(page_number)
    product_data = serializer_class(page_obj.object_list, many=True, context={'request': request}).data
    return Response(list_api_formatter(request, page_obj=page_obj, results=product_data))


@api_view(("GET",))
@_login_required
def orders_detail(request, *a, **k):
    _object = get_object_or_404(Order.objects.filter(user=request.user).prefetch_related(
        'lines',
        'lines__attributes',
        'lines__product__images',
    ).select_related(
        # 'billing_address', 'shipping_address',
    ), pk=k.get('pk'))
    serializer_class = OrderDetailSerializer
    return Response(serializer_class(_object, context={'request': request}).data)


@api_view(("GET",))
@_login_required
def orders_more_detail(request, *a, **k):
    _object = get_object_or_404(Order.objects.filter().prefetch_related(
        'lines',
    ).select_related(
        'billing_address', 'shipping_address'
    ), pk=k.get('pk'))
    serializer_class = OrderMoreDetailSerializer
    return Response(serializer_class(_object, context={'request': request}).data)


@api_view(("POST",))
@_login_required
def order_return_request(request, *a, **k):
    """
    POST {
        "line_ids": [15, 26, 14],
        "reason": "some reason"
    }
    """
    #  Validations
    errors = {"errors": None}
    if type(request.data.get('line_ids', None)) is not list:
        errors['errors'] = "You have to select some lines!"
        return Response(errors, status=400)

    if not request.data.get('reason', None):
        errors['errors'] = "Reason Field is Required"
        return Response(errors, status=400)

    # Body
    _order = get_object_or_404(Order.objects.filter(user=request.user), pk=k.get('pk'))
    if _order.status in get_statuses(1671):
        errors['errors'] = 'Order is not yet delivered!'
        return Response(errors, status=400)
    if _order.status in get_statuses(128+256+512):
        errors['errors'] = 'This order has already been cancelled!'
        return Response(errors, status=400)
    if _order.status in get_statuses(112):
        errors['errors'] = 'You already have initiated another Return!'
        return Response(errors, status=400)
    if _order.is_return_time_expired:
        errors['errors'] = 'Return Time is Over.'
        return Response(errors, status=400)

    line_statuses = _order.lines.filter(status__in=get_statuses(112)).count()

    if line_statuses:
        errors['errors'] = f'You already have initiated / processed  a return request against {line_statuses} items.'
        return Response(errors, status=400)

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
        errors['errors'] = str(e)
        return Response(errors, status=400)
    else:
        return Response(OrderDetailSerializer(_order, context={'request': request}).data, status=200)


@api_view(("POST",))
@_login_required
def order_cancel_request(request, *a, **k):
    """
    POST {
        "reason": "some reason"
    }
    """
    #  Validations
    out_status = 200
    out = {
        "message": None,
        "errors": {

        }
    }

    _order: Order = get_object_or_404(Order.objects.filter(user=request.user), pk=k.get('pk'))

    if not request.data.get('reason', None):
        out['errors'] = "Reason field is Required"
        return Response(out, status=400)

    if not _order.is_cancelable:
        out['errors'] = f"Order with status {_order.status} cannot be cancelled!"
        return Response(out, status=400)

    old_status, new_status = _order.status, settings.ORDER_STATUS_CANCELED
    handler = EventHandler(request.user)

    success_msg = (
        "Order status changed from '%(old_status)s' to "
        "'%(new_status)s'") % {'old_status': old_status,
                               'new_status': new_status}
    try:
        print("Point 01 -- order cancellation")
        handler.handle_order_status_change(_order, new_status, note_msg=success_msg)
        user = request.user.get_full_name() or request.user.username or "User"
        handler.create_note(_order, request.data.get('reason'), note_type=user)

    except PaymentError as e:
        out['errors'] = "Unable to change order status due to payment error"
        return Response(out, status=400)

    except order_exceptions.InvalidOrderStatus:
        # The form should validate against this, so we should only end up
        # here during race conditions.
        out['errors'] = "Unable to change order status as the requested new status is not valid"
        out_status = 400
    else:
        out['message'] = "Order has been cancelled!"
        out_status = 200
    return Response(out, status=out_status)


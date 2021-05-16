from django.conf import settings
from django.core.paginator import Paginator
from django.views.decorators.cache import cache_page
from oscarapi.basket import operations
from oscarapi.basket.operations import prepare_basket, assign_basket_strategy
from rest_framework.decorators import api_view
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from apps.api_set.serializers.basket import WncBasketSerializer
from apps.api_set_v2.serializers.orders import OrderListSerializer
from apps.api_set.views.orders import _login_required   # noqa: underscored import
from apps.basket.models import Basket
from apps.buynow.basket_manager import generate_buy_now_basket
from apps.order.models import Order
from apps.utils.urls import list_api_formatter
from apps.api_set.views.orders import orders_detail     # noqa: using in v2 urls
from lib.cache import cache_library


@api_view(("GET",))
@_login_required
def orders(request, *a, **k):
    cache_key = 'apps.api_set_v2.views.orders?user={}&v=1.0.0'.format

    def _inner():
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
    return _inner()


def clone_order_to_basket(basket: Basket, order_to_get_copied: Order, clear_current_basket: bool = True, ):
    copy_of_basket_lines = list(basket.lines.all())
    error_messages = []
    at_least_one_is_success = False
    if clear_current_basket:
        basket.lines.all().delete()
        basket._lines = None
        basket.refresh_from_db()
    for line in order_to_get_copied.lines.all():
        if line.product is None:
            error_messages.append({
                'id': None,
                'title': line.title,
                'error': "This Product is not selling Right Now",
                'is_a_bug': False,
            })
            continue
        try:
            basket_line, created = basket.add_product(line.product, quantity=line.quantity)
            if not created:
                basket_line.quantity = line.quantity
                basket_line.save()
            at_least_one_is_success = True
        except ValueError as e:
            error_messages.append({
                'id': line.product.id,
                'title': line.product.title,
                'error': str(e),
                'is_a_bug': False,
            })
        except Exception as e:
            error_messages.append({
                'id': line.product.id,
                'title': line.product.title,
                'error': str(e),
                'is_a_bug': True,
            })

    if not at_least_one_is_success:
        # restoring
        for item in copy_of_basket_lines:
            basket_line, created = basket.add_product(product=line.product, quantity=line.quantity)
            if not created:
                basket_line.quantity = line.quantity
                basket_line.save()

        # basket.lines.filter(id__in=[item.id for item in copy_of_basket_lines]).delete()
        basket.reset_offer_applications()
    return basket, error_messages


def get_response_dict_with_basket(basket, request):
    prepare_basket(basket, request)
    ser = WncBasketSerializer(basket, context={"request": request})
    return ser.data


@api_view()
def reorder_to_current_basket(request, *args, **kwargs):
    clear_current_basket = request.GET.get('clear_current_basket', 0) in [1, '1']
    order_to_get_copied: Order = get_object_or_404(Order.objects.all(), **kwargs)
    new_basket, error_messages = clone_order_to_basket(
        request.basket,
        order_to_get_copied,
        clear_current_basket=clear_current_basket
    )
    data = get_response_dict_with_basket(new_basket, request)
    data['error_messages'] = error_messages
    return Response(data)


@api_view()
def reorder_to_temporary_basket(request, *args, **kwargs):
    clear_current_basket = request.GET.get('clear_current_basket', 0) in [1, '1']
    order_to_get_copied: Order = get_object_or_404(Order.objects.all(), **kwargs)
    new_basket, error_messages = clone_order_to_basket(
        generate_buy_now_basket(request),
        order_to_get_copied,
        clear_current_basket=clear_current_basket
    )
    data = get_response_dict_with_basket(new_basket, request)
    data['error_messages'] = error_messages
    return Response(data)

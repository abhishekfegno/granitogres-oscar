from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.views.decorators.cache import cache_page
from oscarapi.basket import operations
from oscarapi.basket.operations import prepare_basket, assign_basket_strategy, apply_offers
from rest_framework.decorators import api_view
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from apps.api_set.serializers.basket import WncBasketSerializer
from apps.api_set_v2.serializers.orders import OrderListSerializer
from apps.api_set.views.orders import _login_required  # noqa: underscored import
from apps.basket.models import Basket
from apps.buynow.basket_manager import generate_buy_now_basket
from apps.order.models import Order
from apps.utils.urls import list_api_formatter
from apps.api_set.views.orders import orders_detail  # noqa: using in v2 urls
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
            'lines',  # calculate any cancelled or cancelling order lines
            # cutting down 60% of queries
        ).order_by('-id')
        paginator = Paginator(queryset, page_size)  # Show 18 contacts per page.
        page_obj = paginator.get_page(page_number)
        product_data = serializer_class(page_obj.object_list, many=True, context={'request': request}).data
        return Response(list_api_formatter(request, page_obj=page_obj, results=product_data))

    return _inner()


# def clone_order_to_basket(basket: Basket, order_to_get_copied: Order, clear_current_basket: bool = True, ):
#     copy_of_basket_lines = list(basket.lines.all())
#     error_messages = []
#     at_least_one_is_success = False
#     if clear_current_basket:
#         basket.lines.all().delete()
#         basket._lines = None
#         basket.refresh_from_db()
#     for line in order_to_get_copied.lines.all():
#         if line.product is None:
#             error_messages.append({
#                 'id': None,
#                 'title': line.title,
#                 'error': "This Product is not selling Right Now",
#                 'is_a_bug': False,
#             })
#             continue
#         try:
#             basket_line, created = basket.add_product(line.product, quantity=line.quantity)
#             if not created:
#                 basket_line.quantity = line.quantity
#                 basket_line.save()
#             at_least_one_is_success = True
#         except ValueError as e:
#             error_messages.append({
#                 'id': line.product.id,
#                 'title': line.product.title,
#                 'error': str(e),
#                 'is_a_bug': False,
#             })
#         except Exception as e:
#             error_messages.append({
#                 'id': line.product.id,
#                 'title': line.product.title,
#                 'error': str(e),
#                 'is_a_bug': True,
#             })
#
#     # if not at_least_one_is_success:
#     #     # restoring
#     #     for item in copy_of_basket_lines:
#     #         basket_line, created = basket.add_product(product=line.product, quantity=line.quantity)
#     #         if not created:
#     #             basket_line.quantity = line.quantity
#     #             basket_line.save()
#     #
#     #     # basket.lines.filter(id__in=[item.id for item in copy_of_basket_lines]).delete()
#     #     basket.reset_offer_applications()
#     basket._lines = None
#     basket.refresh_from_db()
#
#     return basket, error_messages


def do_reorder(basket: Basket, order: Order, request, clear_current_basket: bool=True):  # noqa (too complex (10))
    """
    'Re-order' a previous order.

    This puts the contents of the previous order into your basket
    """
    # Collect lines to be added to the basket and any warnings for lines
    # that are no longer available.
    # basket = request.basket
    lines_to_add = []

    warnings = []
    for line in order.lines.all():
        is_available, reason = line.is_available_to_reorder(basket, request.strategy)
        if is_available:
            lines_to_add.append(line)
        else:
            warnings.append({
                'id': line.product and line.product.id,
                'title': line.title,
                'error': reason,
                'is_generic_cart_error': False,
                'is_a_bug': False,
            })

    # Check whether the number of items in the basket won't exceed the
    # maximum.
    total_quantity = sum([line.quantity for line in lines_to_add])
    is_quantity_allowed, reason = basket.is_quantity_allowed(
        total_quantity)
    if not is_quantity_allowed:
        warnings.append({
            'id': None,
            'title': '-',
            'error': reason,
            'is_generic_cart_error': True,
            'is_a_bug': False,
        })
        return basket, warnings

    if len(lines_to_add) > 0:
        if clear_current_basket:
            basket.lines.all().delete()
            basket._lines = None
            basket.refresh_from_db()

    for line in lines_to_add:
        options = []
        for attribute in line.attributes.all():
            if attribute.option:
                options.append({
                    'option': attribute.option,
                    'value': attribute.value})
        basket.add_product(line.product, line.quantity, options)

    if len(lines_to_add) > 0:
        return basket, warnings
    else:
        warnings.append({
            'id': None,
            'title': '-',
            'error': ("It is not possible to re-order order %(number)s "
                      "as none of its lines are available to purchase") % {'number': order.number},
            'is_generic_cart_error': True,
            'is_a_bug': False,
        })
        return basket, warnings


def get_response_dict_with_basket(basket, request):
    prepare_basket(basket, request)
    ser = WncBasketSerializer(basket, context={"request": request})
    return ser.data


@api_view()
def reorder_to_current_basket(request, *args, **kwargs):
    clear_current_basket = request.GET.get('clear_current_basket', 0) in [1, '1']
    order_to_get_copied: Order = get_object_or_404(Order.objects.all(), **kwargs)
    new_basket, error_messages = do_reorder(
        request.basket,
        order_to_get_copied,
        request,
        clear_current_basket=clear_current_basket
    )
    apply_offers(request, new_basket)
    data = get_response_dict_with_basket(new_basket, request)
    data['error_messages'] = error_messages
    return Response(data)


@api_view()
def reorder_to_temporary_basket(request, *args, **kwargs):
    clear_current_basket = request.GET.get('clear_current_basket', 0) in [1, '1']
    order_to_get_copied: Order = get_object_or_404(Order.objects.all(), **kwargs)
    new_empty_basket = generate_buy_now_basket(request)
    new_basket, error_messages = do_reorder(
        new_empty_basket,
        order_to_get_copied,
        request,
        clear_current_basket=clear_current_basket
    )
    apply_offers(request, new_basket)
    data = get_response_dict_with_basket(new_basket, request)
    data['error_messages'] = error_messages
    return Response(data)

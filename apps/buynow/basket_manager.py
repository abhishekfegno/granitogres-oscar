from oscar.core.loading import get_model
# can be imported from oscarapi
from oscarapi.basket.operations import assign_basket_strategy, apply_offers, flush_and_delete_basket

Basket = get_model('basket', 'Basket')


def generate_buy_now_basket(request, product=None, quantity=1, options=None):
    """This module uses django-oscar-api"""
    buy_now_manager = Basket.buy_now
    old_baskets = buy_now_manager.old_baskets().filter(owner=request.user)

    # Future Compatibility code on alteration to basket.freeze()
    # for _basket in old_baskets:
    #     flush_and_delete_basket(_basket)
    old_baskets.update(status=Basket.FROZEN)

    # if old_baskets and getattr(settings, 'MOVE_BUY_NOW_CANCELLATIONS_TO_CART', False):
    #     for line in old_baskets.lines.all():
    #         request.basket.add_product(line.product, quantity=line.quantity, options=line.options)

    # user can have multiple buy now basket at a time
    basket = buy_now_manager.create(owner=request.user)

    # Assign user onto basket to prevent further SQL queries when
    # basket.owner is accessed.
    basket.owner = request.user
    basket = assign_basket_strategy(basket, request)
    if product:
        basket.add_product(product, quantity=quantity, options=options)
    apply_offers(request, basket)
    return basket





def order_to_basket(order, request):
    from oscarapi.basket.operations import get_basket, prepare_basket, apply_offers

    basket = get_basket(request, prepare=False)
    basket = prepare_basket(basket, request, )

    for line in order.lines.all():
        basket.add_product(line.product, line.quantity, )
    basket = apply_offers(request, basket)
    return basket


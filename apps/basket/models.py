# from oscar.apps.basket.abstract_models import AbstractBasket
from django_oscar_buy_now_api.basket_utils.models import AbstractBuyNowBasket


class Basket(AbstractBuyNowBasket):
    """
    Moking up the real basket
    """

    def add_product(self, product, quantity=1, options=None):
        line, created = super(Basket, self).add_product(product, quantity=quantity, options=options)
        if line.quantity <= 0:
            line.delete()
        return line, created

from oscar.apps.basket.models import *  # noqa isort:skip



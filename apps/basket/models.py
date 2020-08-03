# from oscar.apps.basket.abstract_models import AbstractBasket
from apps.buynow.basket_utils.models import AbstractBuyNowBasket


class Basket(AbstractBuyNowBasket):
    """
    Moking up the real basket
    """

    def add_product(self, product, quantity=1, options=None):
        line, created = super(Basket, self).add_product(product, quantity=quantity, options=options)
        if line.quantity <= 0:
            line.delete()
        self.reset_offer_applications()
        return line, created
    add_product.alters_data = True
    add = add_product

from oscar.apps.basket.models import *  # noqa isort:skip



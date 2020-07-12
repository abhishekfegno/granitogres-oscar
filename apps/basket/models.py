# from oscar.apps.basket.abstract_models import AbstractBasket
from django_oscar_buy_now_api.basket_utils.models import AbstractBuyNowBasket


class Basket(AbstractBuyNowBasket):
    """
    Moking up the real basket
    """


from oscar.apps.basket.models import *  # noqa isort:skip



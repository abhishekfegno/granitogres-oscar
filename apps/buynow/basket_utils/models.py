from django.db import models
from django.utils.translation import gettext_lazy as _
from oscar.apps.basket.abstract_models import AbstractBasket
from apps.buynow.basket_utils.managers import BuyNowBasketManager


class AbstractBuyNowBasket(AbstractBasket):
    BUY_NOW = "Buy Now"
    STATUS_CHOICES = AbstractBasket.STATUS_CHOICES + (
        (BUY_NOW, _("Buy Now - Temporary basket for quick checkout !")),
    )
    status = models.CharField(_("Status"), max_length=128, default=AbstractBasket.OPEN, choices=STATUS_CHOICES)
    buy_now = BuyNowBasketManager()
    editable_statuses = (AbstractBasket.OPEN, AbstractBasket.SAVED, BUY_NOW)

    class Meta(AbstractBasket.Meta):
        abstract = True


__all__ = [
    'AbstractBuyNowBasket',
]






from django.db import models
from django.utils.translation import gettext_lazy as _
from oscar.apps.basket.abstract_models import AbstractBasket

from apps.basket.managers import BuyNowBasketManager


class AbstractBuyNowBasket(AbstractBasket):
    BUY_NOW, OPEN, MERGED, SAVED, FROZEN, SUBMITTED = (
        "Buy Now", "Open", "Merged", "Saved", "Frozen", "Submitted")

    STATUS_CHOICES = (
        (BUY_NOW, _("Buy Now")),
        (OPEN, _("Open - currently active")),
        (MERGED, _("Merged - superceded by another basket")),
        (SAVED, _("Saved - for items to be purchased later")),
        (FROZEN, _("Frozen - the basket cannot be modified")),
        (SUBMITTED, _("Submitted - has been ordered at the checkout")),
    )
    status = models.CharField(_("Status"), max_length=128, default=OPEN, choices=STATUS_CHOICES)

    buy_now = BuyNowBasketManager()
    editable_statuses = (OPEN, SAVED, BUY_NOW)

    class Meta(AbstractBasket.Meta):
        abstract = True


__all__ = [
    'AbstractBuyNowBasket',
]






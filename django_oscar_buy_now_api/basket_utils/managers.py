from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class BuyNowBasketManager(models.Manager):
    status_filter = "Buy Now"

    def get_queryset(self):
        return super().get_queryset().filter(
            status=self.status_filter)

    def get_or_create(self, **kwargs):
        return self.get_queryset().filter_out_expired().get_or_create(
            status=self.status_filter, **kwargs)

    def create(self, **kwargs):
        return self.get_queryset().create(
            status=self.status_filter, **kwargs)

    def filter_out_expired(self):
        buy_now_basket_expiry = getattr(settings, 'BUY_NOW_BASKET_EXPIRY', 60 * 15)  # defaults for 15 minutes
        active_basket_window_start_time = timezone.now() - timedelta(seconds=buy_now_basket_expiry)
        return self.get_queryset().filter(date_created__gte=active_basket_window_start_time)

    def old_baskets(self):
        buy_now_basket_expiry = getattr(settings, 'BUY_NOW_BASKET_EXPIRY', 60 * 15)  # defaults for 15 minutes
        active_basket_window_start_time = timezone.now() - timedelta(seconds=buy_now_basket_expiry)
        return self.get_queryset().filter(date_created__lt=active_basket_window_start_time)


__all__ = [
    'BuyNowBasketManager',
]










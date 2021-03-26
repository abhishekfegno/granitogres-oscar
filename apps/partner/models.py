from django.contrib.gis.db.models import PointField
from django.contrib.gis.forms import MultiPolygonField
from django.core.cache import cache
from django.db.models.signals import post_save
from oscar.apps.partner.abstract_models import AbstractStockRecord, AbstractPartner


class StockRecord(AbstractStockRecord):
    pass


class Partner(AbstractPartner):
    pass


def clear_cache_stock_record(sender, instance, **kwargs):
    cache.delete_pattern("product_list__page:*")
    cache.delete_pattern("product_price_data_lite__key:*")


post_save.connect(clear_cache_stock_record, sender=StockRecord)

from oscar.apps.partner.models import *  # noqa isort:skip



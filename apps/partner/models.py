import math
from django.core.cache import cache
from django.db.models.signals import post_save
from django.utils.translation import gettext_lazy
from oscar.apps.partner.abstract_models import AbstractStockRecord, AbstractPartner
from django.db import models


class StockRecord(AbstractStockRecord):

    cost_price = models.DecimalField(
        "Selling Price (incl. tax)", decimal_places=2, max_digits=12,
        help_text="Just to take the value as input, this will not used for any calculation "
                  "other than calculation `price_excl_tax` field",
        blank=True, null=True)

    price_excl_tax = models.DecimalField(
        gettext_lazy("Selling Price (excl. tax)"), decimal_places=2, max_digits=12,
        blank=True, null=True)

    # Deprecated - will be removed in Oscar 2.1
    price_retail = models.DecimalField(
        gettext_lazy("M.R.P. (retail)"), decimal_places=2, max_digits=12,
        blank=True, null=True)

    def save(self, **kwargs):
        if self.cost_price:
            self.price_excl_tax = float(math.ceil(self.cost_price * 100 / (100 + self.product.tax)))

        super(StockRecord, self).save(**kwargs)

    # @property
    # def tax(self):
    #     return math.ceil(self.product.tax)


class Partner(AbstractPartner):
    pass


def clear_cache_stock_record(sender, instance, **kwargs):

    cache.delete_pattern("product_list__page:{}__page_size*".format(instance.product_id))
    cache.delete('product_price_data__key:product_pk={}*'.format(instance.product_id))
    cache.delete('product_price_data_lite__key:product_pk={}*'.format(instance.product_id))
    cache.delete_pattern("product_price_data_lite__key:*")
    cache.delete_pattern("stock-record-key--prod:{}*".format(instance.product_id))
    cache.delete_pattern("___custom_ProductListSerializer__cached__product:{}*".format(instance.product_id))
    cache.delete_pattern("apps.api_set_v2.views.index*".format(instance.product_id))
    if instance.product and instance.product.is_child:
        cache.delete_pattern(f"stock-record-key--prod:{instance.product.id}*")
        cache.delete_pattern("___custom_ProductListSerializer__cached__product:{}*".format(instance.product.parent_id))
        instance.product.parent.clear_list_caches()


post_save.connect(clear_cache_stock_record, sender=StockRecord)


from oscar.apps.partner.models import *  # noqa isort:skip



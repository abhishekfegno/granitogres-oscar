from oscar.apps.partner import strategy
from oscar.apps.partner.availability import Unavailable, Available, StockRequired as StockRequiredAvailability

from apps.partner.strategy_set.utils.tax import IndianGST
from apps.partner.strategy_set.utils.stock_records import (
    ZoneBasedStockRecord
)


class ZoneBasedIndianPricingStrategy(ZoneBasedStockRecord, IndianGST,
                                     strategy.StockRequired, strategy.Structured):

    def __init__(self, zone, request=None, user=None, **kwargs):
        super().__init__(request)
        if not request and user:
            self.user = user
        self.zone_id = zone

    def availability_policy(self, product, stockrecord):
        if not stockrecord:
            return Unavailable()
        if not product.get_product_class().track_stock:
            return Available()
        else:
            return StockRequiredAvailability(stockrecord.net_stock_level)


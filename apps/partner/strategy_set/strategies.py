from oscar.apps.partner import strategy
from oscar.apps.partner.availability import Unavailable, Available, StockRequired as StockRequiredAvailability

from apps.partner.strategy_set.utils.tax import IndianGST
from apps.availability.pincode.oscar_strategy_mixins import PincodeStockRecord
from apps.partner.strategy_set.utils.stock_records import (
    MinimumPriceStockRecord, ZoneBasedStockRecord, UseFirstStockRecord)


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


class IndianStrategyUsingPincode(PincodeStockRecord, IndianGST,  strategy.StockRequired, strategy.Structured):

    def __init__(self, request=None, user=None, **kwargs):
        super().__init__(request)
        if not request and user:
            self.user = user


class MinimumValueStrategy(MinimumPriceStockRecord, IndianGST, strategy.StockRequired, strategy.Structured):
    """
    Strategy Used For Displaying Minimum Price. But this will not be available until you have a proper
    PinCode to Select A StockRecord
    """
    def __init__(self, request=None, user=None, **kwargs):
        super().__init__(request)
        if not request:
            self.user = user


class MinimumValueStrategyWithOutOfStock(MinimumValueStrategy):

    def availability_policy(self, product, stockrecord):
        return Unavailable()

    def parent_availability_policy(self, product, children_stock):
        return Unavailable()



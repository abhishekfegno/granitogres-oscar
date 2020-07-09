from oscar.apps.partner import strategy
from oscar.core.loading import get_class

from apps.partner.strategy_set.indian import IndianGST

Unavailable = get_class('partner.availability', 'Unavailable')


class PinCodeNotFound(Unavailable):
    message = 'no_pin_code'


class MinimumPriceStockRecord(object):

    def select_stockrecord(self, product):
        return product.stockrecords.order_by('price_excl_tax').first()


class MinimumValueStrategy(MinimumPriceStockRecord, IndianGST, strategy.StockRequired, strategy.Structured):
    """
    Strategy Used For Displaying Minimum Price. But this will not be available until you have a proper
    PinCode to Select A StockRecord
    """
    def __init__(self, request=None, user=None, **kwargs):
        super().__init__(request)
        if not request and user:
            self.user = user
        # print(f"MinimumValueStrategy > pin not set")

    # def availability_policy(self, product, stockrecord):
    #     return PinCodeNotFound()
    #
    # def parent_availability_policy(self, product, children_stock):
    #     return PinCodeNotFound()



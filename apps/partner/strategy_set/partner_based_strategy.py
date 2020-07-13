from decimal import Decimal

from oscar.apps.partner import strategy

from apps.availability.oscar_strategy_mixins import PincodeStockRecord
from apps.partner.models import StockRecord


class IndianGST(strategy.FixedRateTax):
    rate = Decimal("0.18")


class PreselectedPartnerStockRecord(object):
    request = None
    partner_id = None

    def select_stockrecord(self, product):
        stock_records = StockRecord.objects.filter(partner_id=self.partner_id, product=product)
        for stock_record in stock_records:
            return stock_record


class PartnerBasedIndianStrategy(PreselectedPartnerStockRecord, IndianGST,
                                 strategy.StockRequired, strategy.Structured):

    def __init__(self, partner, request=None, user=None, **kwargs):
        super().__init__(request)
        self.partner_id = partner



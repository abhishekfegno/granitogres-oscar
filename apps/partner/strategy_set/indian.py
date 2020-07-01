from decimal import Decimal

from oscar.apps.partner import strategy

from apps.availability.oscar_strategy_mixins import PincodeStockRecord


class IndianGST(strategy.FixedRateTax):
    rate = Decimal("0.18")


class IndianStrategyUsingPincode(PincodeStockRecord, IndianGST,  strategy.StockRequired, strategy.Structured):

    def __init__(self, request=None, user=None, **kwargs):
        super().__init__(request)
        if not request and user:
            self.user = user
        print(f"IndianStrategyUsingPincode > {request.session['pincode']}")



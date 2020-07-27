from decimal import Decimal

from oscar.apps.partner import strategy


class IndianGST(strategy.FixedRateTax):
    rate = Decimal("0.18")

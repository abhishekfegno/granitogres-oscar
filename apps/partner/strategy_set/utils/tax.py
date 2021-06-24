from decimal import Decimal

from oscar.apps.partner import strategy


class IndianGST(strategy.FixedRateTax):

    rate = Decimal("0.18")

    def get_rate(self, product, stockrecord):
        """
        This method serves as hook to be able to plug in support for varying tax rates
        based on the product.

        """
        return product.tax_value


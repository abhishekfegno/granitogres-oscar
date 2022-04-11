import math

from oscar.apps.partner.availability import Unavailable, Available, Base
from oscar.apps.partner.prices import FixedPrice, TaxInclusiveFixedPrice
from oscar.apps.partner.strategy import UK, UseFirstStockRecord, StockRequired, FixedRateTax, Structured, \
    StockRequiredAvailability, PurchaseInfo, UnavailablePrice, NoTax
from oscar.core.utils import get_default_currency

from apps.availability.models import Zones
from apps.partner.prices import TaxInclusiveSellingOrientedFixedPrice
from apps.partner.strategy_set.strategies import ZoneBasedIndianPricingStrategy
from decimal import Decimal as D

from apps.partner.strategy_set.utils.stock_records import ZoneBasedStockRecord, MinimumPriceStockRecord


class AbchauzIndiaFixedRateTax(FixedRateTax):
    """
    Pricing policy mixin for use with the ``Structured`` base strategy.  This
    mixin applies a fixed rate tax to the base price from the product's
    stockrecord.  The price_incl_tax is quantized to two decimal places.
    Rounding behaviour is Decimal's default
    """
    rate = D('0')  # Subclass and specify the correct rate
    exponent = D('0.01')  # Default to two decimal places

    def pricing_policy(self, product, stockrecord):
        if not stockrecord or stockrecord.price_excl_tax is None:
            return UnavailablePrice()
        rate = self.get_rate(product, stockrecord)
        exponent = self.get_exponent(stockrecord)
        tax = (stockrecord.price_excl_tax * rate).quantize(exponent)
        return TaxInclusiveSellingOrientedFixedPrice(
            currency=stockrecord.price_currency,
            incl_tax=int(math.floor(stockrecord.price_excl_tax + tax)),
            tax=tax)

    def parent_pricing_policy(self, product, children_stock):
        stockrecords = [x[1] for x in children_stock if x[1] is not None]
        if not stockrecords:
            return UnavailablePrice()

        # We take price from first record
        stockrecord = stockrecords[0]
        rate = self.get_rate(product, stockrecord)
        exponent = self.get_exponent(stockrecord)
        tax = (stockrecord.price_excl_tax * rate).quantize(exponent)

        return TaxInclusiveSellingOrientedFixedPrice(
            currency=stockrecord.price_currency,
            incl_tax=int(math.floor(stockrecord.price_excl_tax + tax)),
            tax=tax)


class MessagedUnavailable(Base):
    """
    Policy for when a product is unavailable
    """
    code = 'unavailable'
    message = "Unavailable"

    def __init__(self, message=None):
        if message:
            self.message = message


class ABCHauzPricing(ZoneBasedStockRecord, StockRequired, AbchauzIndiaFixedRateTax, Structured):
    """
    Sample strategy for the UK that:

    - uses the first stockrecord for each product (effectively assuming
        there is only one).
    - requires that a product has stock available to be bought
    - applies a fixed rate of tax on all products

    This is just a sample strategy used for internal development.  It is not
    recommended to be used in production, especially as the tax rate is
    hard-coded.
    """

    def __init__(self, request=None, user=None, **kwargs):
        super().__init__(request)
        self.user = user or self.user
        self.kwargs = kwargs

    def get_rate(self, product, stockrecord=None):
        return D(str(product.tax/100))

    def fetch_for_product(self, product, stockrecord=None):
        """
        Return the appropriate ``PurchaseInfo`` instance.
        This method is not intended to be overridden.
        """

        if stockrecord is None:
            stockrecord = self.select_stockrecord(product)

        pinfo = PurchaseInfo(
            price=self.pricing_policy(product, stockrecord),
            availability=self.availability_policy(product, stockrecord),
            stockrecord=stockrecord)
        return pinfo

    def fetch_for_parent(self, product):
        # Select children and associated stockrecords
        children_stock = self.select_children_stockrecords(product)
        return PurchaseInfo(
            price=self.parent_pricing_policy(product, children_stock),
            availability=self.parent_availability_policy(
                product, children_stock),
            stockrecord=None)

    def availability_policy(self, product, stockrecord):
        if not stockrecord:
            return Unavailable()
        if product.get_product_class() and not product.get_product_class().track_stock:
            return Available()
        else:
            is_permitted, message = True, ''        # todo some border defining logic. like kerala only or something.
            if is_permitted:
                return StockRequiredAvailability(stockrecord.net_stock_level)
            else:
                return MessagedUnavailable(message)


class GranitogresPricing(UseFirstStockRecord, FixedRateTax, Structured):
    rate = D('0.18')  # Subclass and specify the correct rate

    def __init__(self, request=None, user=None, **kwargs):
        super().__init__(request)
        self.user = user or self.user
        self.kwargs = kwargs

    def availability_policy(self, product, stockrecord):
        return Available()

    def parent_availability_policy(self, product, children_stock):
        return Available()

    def pricing_policy(self, product, stockrecord):
        rate = self.get_rate(product, stockrecord)
        exponent = self.get_exponent(stockrecord)
        tax = (stockrecord.price_excl_tax * rate).quantize(exponent)
        return TaxInclusiveSellingOrientedFixedPrice(
            currency=get_default_currency(),
            incl_tax=int(math.floor(stockrecord.price_excl_tax + tax)),
            tax=tax)

    def fetch_for_product(self, product, stockrecord=None):
        """
        Return the appropriate ``PurchaseInfo`` instance.
        This method is not intended to be overridden.
        """

        if stockrecord is None:
            stockrecord = self.select_stockrecord(product)

        pinfo = PurchaseInfo(
            price=self.pricing_policy(product, stockrecord),
            availability=self.availability_policy(product, stockrecord),
            stockrecord=stockrecord)
        return pinfo

    def fetch_for_parent(self, product):
        # Select children and associated stockrecords
        children_stock = self.select_children_stockrecords(product)
        return PurchaseInfo(
            price=self.parent_pricing_policy(product, children_stock),
            availability=self.parent_availability_policy(
                product, children_stock),
            stockrecord=None)


class Selector(object):
    """
    Custom selector to return a Indian-specific strategy that charges GST
    """

    def strategy(self, request=None, user=None, **kwargs):
        return GranitogresPricing(request=request, user=user, **kwargs)




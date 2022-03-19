from oscar.apps.partner.availability import Unavailable, Available
from oscar.apps.partner.prices import FixedPrice, TaxInclusiveFixedPrice
from oscar.apps.partner.strategy import UK, UseFirstStockRecord, StockRequired, FixedRateTax, Structured, \
    StockRequiredAvailability, PurchaseInfo, UnavailablePrice

from apps.availability.models import Zones
from apps.partner.strategy_set.strategies import ZoneBasedIndianPricingStrategy
from decimal import Decimal as D

from apps.partner.strategy_set.utils.stock_records import ZoneBasedStockRecord


class ABCHauzPricing(ZoneBasedStockRecord, StockRequired, FixedRateTax, Structured):
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

    def availability_policy(self, product, stockrecord):
        if not stockrecord:
            return Unavailable()
        if product.get_product_class() and not product.get_product_class().track_stock:
            return Available()
        else:
            return StockRequiredAvailability(stockrecord.net_stock_level)


class Selector(object):
    """
    Custom selector to return a Indian-specific strategy that charges GST
    """

    def strategy(self, request=None, user=None, **kwargs):
        zone = 0
        if request and request.GET.get('pincode'):
            from apps.availability.facade import ZoneFacade, get_zone_from_pincode
            _zone = get_zone_from_pincode(request.GET.get('pincode'))
            zone: int = _zone.id
        if zone is None:
            zone: int = request.session.get('zone')  # zone => Zone.pk

        return ABCHauzPricing(request=request, user=user, zone=zone, **kwargs)

        # zone = kwargs.get('zone') or (request and request.session.get('zone'))
        #
        # # TODO: FOR DEBUGGING PURPOSES
        # if not zone:
        #     zone = Zones.objects.filter().last()
        #     if zone:
        #         zone = zone.id
        #         if request:
        #             request.session['zone'] = zone
        # if not zone and (not request and user):
        #     last_location = user.location_set.filter(is_active=True).last()
        #     if last_location and last_location.zone_id:
        #         zone = last_location.zone_id
        #         request.session['zone'] = zone
        #
        # return ZoneBasedIndianPricingStrategy(zone, request=request, user=user, **kwargs)
        #

from oscar.apps.partner.strategy import UK

from apps.availability.models import Zones
from apps.partner.strategy_set.strategies import ZoneBasedIndianPricingStrategy
from decimal import Decimal as D


class Selector(object):
    """
    Custom selector to return a Indian-specific strategy that charges GST
    """

    def strategy(self, request=None, user=None, **kwargs):
        strat = UK(request=None)
        strat.rate = D('0.20')
        return strat

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

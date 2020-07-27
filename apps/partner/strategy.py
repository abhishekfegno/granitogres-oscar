from apps.partner.strategy_set.strategies import ZoneBasedIndianPricingStrategy
from apps.partner.strategy_set.strategies import MinimumValueStrategy


class Selector(object):
    """
    Custom selector to return a Indian-specific strategy that charges GST
    """

    def strategy(self, request=None, user=None, **kwargs):

        if kwargs.get('zone'):
            return ZoneBasedIndianPricingStrategy(kwargs.get('zone'), request=request, user=user, **kwargs)

        if request and request.session.get('zone'):
            zone = request.session['zone']
            return ZoneBasedIndianPricingStrategy(zone, request=request, user=user, **kwargs)

        if not request and user:
            last_location = user.location_set.filter(is_active=True).last()
            if last_location and last_location.zone_id:
                return ZoneBasedIndianPricingStrategy(last_location.zone_id, request=request, user=user, **kwargs)

        return MinimumValueStrategy()


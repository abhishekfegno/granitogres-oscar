from apps.partner.strategy_set.indian import IndianStrategyUsingPincode
from apps.partner.strategy_set.minimum import MinimumValueStrategy
from apps.partner.strategy_set.partner_based_strategy import PartnerBasedIndianStrategy


class Selector(object):
    """
    Custom selector to return a Indian-specific strategy that charges GST
    """

    def strategy(self, request=None, user=None, **kwargs):
        # if request and request.session.get('pincode'):
        #     return IndianStrategyUsingPincode(request=request, user=user, **kwargs)
        return MinimumValueStrategy()

    def partner_based_strategy(self, partner):
        return PartnerBasedIndianStrategy(partner)


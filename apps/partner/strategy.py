
from apps.partner.strategy_set.indian import IndianStrategyUsingPincode
from apps.partner.strategy_set.minimum import MinimumValueStrategy


class Selector(object):
    """
    Custom selector to return a Indian-specific strategy that charges GST
    """
    def strategy(self, request=None, user=None, **kwargs):
        # if request and request.session.get('pincode'):
        #     return IndianStrategyUsingPincode(request=request, user=user, **kwargs)
        return MinimumValueStrategy()


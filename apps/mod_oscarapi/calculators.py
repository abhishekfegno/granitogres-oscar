from oscar.core import prices


class OrderTotalCalculator(object):
    """
    Calculator class for calculating the order total.
    """

    def __init__(self, request=None):
        # We store a reference to the request as the total may
        # depend on the user or the other checkout data in the session.
        # Further, it is very likely that it will as shipping method
        # always changes the order total.
        self.request = request

    def calculate(self, basket, shipping_charge, **kwargs):
        # we are not considering tax for shipping.
        excl_tax = basket.total_excl_tax + shipping_charge.incl_tax
        basket_taxed = basket.total_incl_tax if basket.is_tax_known else 0
        ship_taxed = shipping_charge.incl_tax if shipping_charge.is_tax_known else 0
        incl_tax = basket_taxed + ship_taxed
        return prices.Price(
            currency=basket.currency,
            excl_tax=excl_tax,
            incl_tax=incl_tax,
        )

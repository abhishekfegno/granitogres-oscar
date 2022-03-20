from oscar.apps.partner.prices import FixedPrice


class TaxInclusiveSellingOrientedFixedPrice(FixedPrice):
    """
    Specialised version of FixedPrice that must have tax passed.  It also
    specifies that offers should use the tax-inclusive price (which is the norm
    in the UK).
    """
    incl_tax: float = None
    exists = is_tax_known = True

    def __init__(self, currency, incl_tax, tax):    #noqa
        self.currency = currency
        self.incl_tax = incl_tax
        self.tax = tax

    @property
    def excl_tax(self):
        return self.incl_tax - self.tax

    @property
    def effective_price(self):
        return self.incl_tax




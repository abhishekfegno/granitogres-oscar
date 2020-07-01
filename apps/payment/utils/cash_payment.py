from bpython.translations import _
from oscarapicheckout import states
from oscarapicheckout.methods import Cash as CoreCash


class Cash(CoreCash):
    """
    Accepts Cash on Delivery / Card on Delivery Payments overriding example payment from oscarapicheckout.
    """


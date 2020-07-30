from bpython.translations import _
from oscarapicheckout import states
from oscarapicheckout.methods import Cash as CoreCash

from apps.payment.utils import PaymentRefundMixin


class Cash(PaymentRefundMixin, CoreCash):
    """
    Accepts Cash on Delivery / Card on Delivery Payments overriding example payment from oscarapicheckout.
    """


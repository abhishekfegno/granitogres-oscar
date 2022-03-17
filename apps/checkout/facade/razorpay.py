from django.conf import settings
import razorpay

from apps.checkout.facade.abstract_facade import AbstractFacade


class RazorPayFacade(AbstractFacade):
    def __init__(self):
        super().__init__()
        self.session = razorpay.Client(auth=(settings.RAZOR_PAY_PUBLIC_KEY, settings.RAZOR_PAY_SECRET_KEY))

    @staticmethod
    def get_friendly_decline_message(error):
        return 'The transaction was declined by your bank - please check your bankcard details and try again'

    @staticmethod
    def get_friendly_error_message(error):
        return 'An error occurred when communicating with the payment gateway.'

    def charge(self,
               order_number, total_amount_incl_tax, token, currency=settings.PAYMENT_CURRENCY,
               description=None, metadata=None, **kwargs):
        return self.session.payment.capture(token, total_amount_incl_tax)




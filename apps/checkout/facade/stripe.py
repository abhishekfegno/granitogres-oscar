from django.conf import settings
from oscar.apps.payment.exceptions import UnableToTakePayment, InvalidGatewayRequestError
from .. import PAYMENT_METHOD_STRIPE, PAYMENT_EVENT_PURCHASE, STRIPE_EMAIL, STRIPE_TOKEN

import stripe

from apps.checkout.facade.abstract_facade import AbstractFacade


class StripeFacade(AbstractFacade):

    def __init__(self):
        stripe.api_key = settings.RAZORPAY_SECRET_KEY

    @staticmethod
    def get_friendly_decline_message(error):
        return 'The transaction was declined by your bank - please check your bankcard details and try again'

    @staticmethod
    def get_friendly_error_message(error):
        return 'An error occurred when communicating with the payment gateway.'

    def charge(self,
               order_number,
               total,
               token,
               currency=settings.PAYMENT_CURRENCY,
               description=None,
               metadata=None,
               **kwargs):
        try:
            return stripe.Charge.create(
                amount=(total.incl_tax * 100).to_integral_value(),
                currency=currency,
                card=token,
                description=description,
                metadata=(metadata or {'order_number': order_number}),
                **kwargs).id
        except stripe.CardError as e:
            raise UnableToTakePayment(self.get_friendly_decline_message(e))
        except stripe.StripeError as e:
            raise InvalidGatewayRequestError(self.get_friendly_error_message(e))

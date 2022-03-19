from django.conf import settings
from oscar.apps.payment.models import SourceType
from oscar.core.loading import get_model
from oscar.templatetags.currency_filters import currency
from apps.checkout.facade.razorpay import RazorPayFacade as Facade

from apps.checkout import forms, RAZOR_PAY_TOKEN, PAYMENT_METHOD_STRIPE, PAYMENT_EVENT_PURCHASE
from apps.payment.utils.razorpay_payment import RazorPay

SITE_NAME = 'ABC Hauz'
Source = get_model('payment', 'Source')


class RazorPayPaymentMixin(object):

    def get_stripe_context_data(self, **kwargs):
        ctx = {}
        if self.preview:    # noqa:
            ctx['token_form'] = forms.RazorPayTokenForm(self.request.POST) # noqa:
        else:
            ctx['payment_publishable_key'] = settings.STRIPE_PUBLIC_KEY
        return ctx

    def handle_razor_pay_payment(self,
                              order_number, total, token,
                              currency=settings.PAYMENT_CURRENCY,
                              description=None,
                              metadata=None, **kwargs):

        razor_pay_ref = Facade().charge(
            order_number,
            total,
            token=self.request.POST[RAZOR_PAY_TOKEN], # noqa:
            description=self.payment_description(order_number, total, **kwargs), # noqa:
            metadata=self.payment_metadata(order_number, total, **kwargs) # noqa:
        )

        source_type, __ = SourceType.objects.get_or_create(name=RazorPay.name, code=RazorPay.code)
        source = Source(
            source_type=source_type,
            currency=settings.PAYMENT_CURRENCY,
            amount_allocated=total.incl_tax,
            amount_debited=total.incl_tax,
            reference=razor_pay_ref)
        self.add_payment_source(source)                 # noqa:
        self.add_payment_event(PAYMENT_EVENT_PURCHASE, total.incl_tax)      # noqa:

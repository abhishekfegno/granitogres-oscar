from django.conf import settings
from oscar.core.loading import get_model
from oscar.templatetags.currency_filters import currency
from apps.checkout.facade.stripe import StripeFacade as Facade

from apps.checkout import forms, STRIPE_TOKEN, PAYMENT_METHOD_STRIPE, PAYMENT_EVENT_PURCHASE

SITE_NAME = 'WoodN\'Cart'
SourceType = get_model('payment', 'SourceType')
Source = get_model('payment', 'Source')

# https://groups.google.com/forum/?fromgroups#!topic/django-oscar/Cr8sBI0GBu0


class StripePaymentMixin(object):

    def get_stripe_context_data(self, **kwargs):
        ctx = {}
        if self.preview:    # noqa:
            ctx['token_form'] = forms.StripeTokenForm(self.request.POST) # noqa:
        else:
            ctx['payment_publishable_key'] = settings.STRIPE_PUBLIC_KEY
        return ctx

    def handle_stripe_payment(self, order_number, total, **kwargs):
        stripe_ref = Facade().charge(
            order_number,
            total,
            card=self.request.POST[STRIPE_TOKEN], # noqa:
            description=self.payment_description(order_number, total, **kwargs), # noqa:
            metadata=self.payment_metadata(order_number, total, **kwargs) # noqa:
        )

        source_type, __ = SourceType.objects.get_or_create(name=PAYMENT_METHOD_STRIPE)
        source = Source(
            source_type=source_type,
            currency=settings.PAYMENT_CURRENCY,
            amount_allocated=total.incl_tax,
            amount_debited=total.incl_tax,
            reference=stripe_ref)
        self.add_payment_source(source)                 # noqa:
        self.add_payment_event(PAYMENT_EVENT_PURCHASE, total.incl_tax)      # noqa:

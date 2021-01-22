from django.conf import settings
from oscar.core.loading import get_model
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from oscar.apps.checkout.views import PaymentDetailsView as CorePaymentDetailsView
from oscar.templatetags.currency_filters import currency
from apps.checkout.facade.razorpay import RazorPayFacade as Facade

from . import PAYMENT_METHOD_STRIPE, PAYMENT_EVENT_PURCHASE, STRIPE_EMAIL, STRIPE_TOKEN, RAZOR_PAY_TOKEN

from apps.checkout import forms
from .payment_view_mixins.cod_view import CodPaymentMixin
from .payment_view_mixins.razor_pay_view import RazorPayPaymentMixin
from .payment_view_mixins.stripe_view import StripePaymentMixin

SourceType = get_model('payment', 'SourceType')
Source = get_model('payment', 'Source')
SITE_NAME = 'Grocery'


class PaymentDetailsView(RazorPayPaymentMixin, CodPaymentMixin, CorePaymentDetailsView):
    # add_additional_context = []

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(PaymentDetailsView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(PaymentDetailsView, self).get_context_data( **kwargs)
        for handle in self.add_additional_context:
            if hasattr(self, handle):
                ctx = {**getattr(self, handle)(), **ctx}
        ctx['order_total_incl_tax_cents'] = (
                ctx['order_total'].incl_tax * 100
        ).to_integral_value()
        ctx['shop_name'] = f'{SITE_NAME}'
        ctx['description'] = f'Payment with {SITE_NAME} with an amount of {currency(ctx["order_total"].incl_tax)} INR '

        return ctx

    def handle_payment(self, order_number, total, **kwargs):
        if self.request.POST['payment_method'] == 'cod':
            self.add_additional_context.append('get_cod_context_data')
            return self.handle_cod(
                order_number, total,
                description=self.payment_description(order_number, total, **kwargs),
                metadata=self.payment_metadata(order_number, total, **kwargs),
                **kwargs)

        if self.request.POST['payment_method'] == 'stripe':
            self.add_additional_context.append('get_stripe_context_data')
            return self.handle_stripe_payment(
                order_number, total,
                description=self.payment_description(order_number, total, **kwargs),
                metadata=self.payment_metadata(order_number, total, **kwargs),
                **kwargs)

        if self.request.POST['payment_method'] == 'razorpay':
            self.add_additional_context.append('get_razorpay_context_data')
            return self.handle_razor_pay_payment(
                order_number, total, token=self.POST[RAZOR_PAY_TOKEN],
                description=self.payment_description(order_number, total, **kwargs),
                metadata=self.payment_metadata(order_number, total, **kwargs),
                **kwargs)

    def payment_description(self, order_number, total, **kwargs):
        from datetime import datetime
        from pytz import timezone
        ist = timezone('Asia/Kolkata')
        ist_time = datetime.now(ist)
        return f"Payment with {SITE_NAME} against order #{order_number} with an amount of " \
               f" {total.incl_tax} INR on {ist_time.strftime('%Y-%m-%d_%H-%M-%S')}"

    def payment_metadata(self, order_number, total, **kwargs):
        return {'order_number': order_number, 'amount': total.incl_tax}










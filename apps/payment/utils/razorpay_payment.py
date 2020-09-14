import requests
from django.conf import settings
from django.utils import timezone
from oscar.apps.payment.models import Source
from oscarapicheckout import states
from oscarapicheckout.methods import PaymentMethod

from apps.payment.models import PaymentGateWayResponse
from apps.payment.utils import PaymentRefundMixin
import razorpay


class RazorPay(PaymentRefundMixin, PaymentMethod):
    """
    Cash payments are an example of how to implement a payment method plug-in. It
    doesn't do anything more than record a transaction and payment source.
    """
    # Translators: Description of payment method in checkout
    name = 'Razor Pay'
    code = 'razor_pay'

    def __init__(self):
        self.client = razorpay.Client(autn=(settings.RAZOR_PAY_PUBLIC_KEY, settings.RAZOR_PAY_SECRET_KEY))
        self.client.set_app_details({"title": "Shopprix - Super Center", "version": "0.9.0"})

    def _record_payment(self, request, order, method_key, amount, reference, **kwargs):
        """
        Get Payment Source, Calculate amount to allocate, calculate, amount to debit,

        MARKER: Create Payment and Payment State,
        if Payment State is complete:
            then:: MARKER:  Debit the amount, create curresponding event and update line quantities.
        """
        source = self.get_source(order, reference)
        amount_to_allocate = amount - source.amount_allocated
        source.allocate(amount_to_allocate, reference)
        amount_to_debit = amount - source.amount_debited
        payment_state = self._get_external_payment(source, amount, reference, )

        if payment_state.status == states.COMPLETE:
            source.debit(amount_to_debit, reference)
            event = self.make_debit_event(order, amount_to_debit, reference)
            for line in order.lines.all():
                self.make_event_quantity(event, line, line.quantity)
        return payment_state

    def _get_external_payment(self, source, amount, reference, description=None):
        """
        Get Client, GEt Payment Gateway Rrsponse,
        """
        client = self.client
        # EXTERNAL PAYMENT      # espicially for the purpose of COD.
        pgr = PaymentGateWayResponse()
        pgr.transaction_id = reference
        pgr.transaction_type = PaymentGateWayResponse.PURCHASE
        pgr.amount = amount
        pgr.source = source
        pgr.description = description
        pgr.payment_status = False
        pgr._response = {}
        # pgr.save()

        try:
            # success case
            response = client.payment.capture(reference, float(amount))    # noqa
            pgr._response = response
            # LOGGING RESPONSE
            pgr.payment_status = True
            pgr.parent_transaction = None
            pgr.save()
        except (
                razorpay.errors.BadRequestError, # noqa
                razorpay.errors.ServerError, # noqa
                razorpay.errors.SignatureVerificationError, # noqa
                requests.exceptions.ConnectionError,
        ) as e:
            # payment Rejected Error
            pgr.payment_status = False
            pgr._response = {'id': reference, 'entity': 'payment', 'amount': amount, 'currency': source.currency,
                             'status': 'already_captured', 'error': str(e)}
            pgr.save()
            return states.Declined(source.amount_debited, source_id=source.pk)
        else:
            return states.Complete(source.amount_debited, source_id=source.pk)

    def create_actual_refund_with_gateway(self, source: Source, amount):
        client = self.client
        reference = source.reference
        order = source.order
        payment_pgr = PaymentGateWayResponse.objects.get(transaction_id=reference)

        # EXTERNAL PAYMENT
        payment_response = client.payment.fetch(reference)
        if payment_response['refund_status'] not in [None, 'partial']:
            return
        payment_pgr._response = payment_response
        max_refundable_amount = payment_response['amount'] - payment_response['amount_refunded']
        if amount > max_refundable_amount:
            msg = f"""The Amount {source.currency} {amount}/- is more than the 
                    {source.currency} {max_refundable_amount} /-.  
                    The total amount of this order #{order.number} is 
                    {source.currency}  {payment_response['amount']}/-"""

            if payment_response['amount_refunded']:
                msg += f" and we already have refunded {source.currency} {payment_response['amount_refunded']} "
            msg += f""". In this situation, we could not proceed payment refund with the given amount. 
                    (Payment Reference : {reference})"""
            raise Exception(msg)

        pgr = PaymentGateWayResponse(
            transaction_type=PaymentGateWayResponse.REFUND,
            amount=amount,
            source=source,
            description=f'Refund of {source.currency} {amount} /- against Order ({source.order.number}) on {timezone.now()}',
            parent_transaction=payment_pgr,
        )
        try:
            # success case
            response = client.payment.refund(reference, str(amount)) # noqa
            pgr._response = response
            pgr.transaction_id = response['id']

            # LOGGING RESPONSE
            pgr.payment_status = True
            pgr.save()
            return states.Complete(source.amount_debited, source_id=source.pk)
        except (
                razorpay.errors.BadRequestError,  # noqa
                razorpay.errors.ServerError, # noqa
                razorpay.errors.SignatureVerificationError, # noqa
                requests.exceptions.ConnectionError,
        ) as e:
            # payment Rejected Error
            pgr.payment_status = False
            pgr._response = {'id': reference, 'entity': 'payment', 'amount': amount, 'currency': source.currency,
                             'status': 'already_captured', 'error': str(e)}
            pgr.save()
            return states.Declined(source.amount_debited, source_id=source.pk)



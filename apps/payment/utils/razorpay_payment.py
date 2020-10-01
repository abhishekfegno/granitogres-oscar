import time

import requests
from django.conf import settings
from django.utils import timezone
from oscar.apps.payment.models import Source
from oscarapicheckout import states
from oscarapicheckout.methods import PaymentMethod, Transaction

from apps.payment.models import PaymentGateWayResponse
from apps.payment.utils import PaymentRefundMixin
import razorpay

from lib.exceptions import AlertException


class RazorPay(PaymentRefundMixin, PaymentMethod):
    """
    Cash payments are an example of how to implement a payment method plug-in. It
    doesn't do anything more than record a transaction and payment source.
    """
    # Translators: Description of payment method in checkout
    name = 'Razor Pay'
    code = 'razor_pay'

    def __init__(self):
        self.client = razorpay.Client(auth=(settings.RAZOR_PAY_PUBLIC_KEY, settings.RAZOR_PAY_SECRET_KEY))
        self.client.set_app_details({"title": f"Django", "version": "2.2.12"})

    def get_reference_from_source(self, source):
        if source.reference and source.reference.startswith('pay_'):
            return source.reference
        ref = source.transactions.filter(txn_type=Transaction.DEBIT, reference__istartswith='pay_').first()
        if ref:
            return ref

    def _record_payment(self, request, order, method_key, amount, reference, **kwargs):
        """
        Get Payment Source, Calculate amount to allocate, calculate, amount to debit,

        MARKER: Create Payment and Payment State,
        if Payment State is complete:
            then:: MARKER:  Debit the amount, create curresponding event and update line quantities.
        """
        reference = request.data['payment']['razor_pay']['razorpay_payment_id']
        source = self.get_source(order, reference)
        amount_to_allocate = amount - source.amount_allocated
        source.allocate(amount_to_allocate, reference)
        amount_to_debit = amount - source.amount_debited
        payment_state = self._get_external_payment(source, amount, reference=reference, )
        if payment_state.status == states.COMPLETE:
            source.debit(amount_to_debit, reference=reference)
            event = self.make_debit_event(order, amount_to_debit, reference=reference)
            for line in order.lines.all():
                self.make_event_quantity(event, line, line.quantity)
        return payment_state

    def _get_external_payment(self, source, amount, reference, description=None):
        """
        Get Client, GEt Payment Gateway Rrsponse,reference
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
        pgr.response = {}
        # pgr.save()
        try:
            # success case
            fetch_resp = client.payment.fetch(reference)
            if fetch_resp['status'] == 'authorized':
                fetch_resp = client.payment.capture(reference, int(amount))
            response = fetch_resp
            pgr.response = response
            pgr.description = description

            # LOGGING RESPONSE
            pgr.payment_status = fetch_resp['status'] == 'captured'
            pgr.parent_transaction = None
            pgr.save()
            if fetch_resp['status'] == 'refund':
                raise razorpay.errors.BadRequestError('Refund Triggered Already.')
            elif fetch_resp['status'] == 'failed':
                raise razorpay.errors.BadRequestError('Transaction Failed.')

            pgr.response = response
            pgr.description = description

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
            pgr.response = {'id': reference, 'entity': 'payment', 'amount': amount, 'currency': source.currency,
                             'status': 'already_captured', 'error': str(e)}
            pgr.save()
            return states.Declined(source.amount_debited, source_id=source.pk)
        else:
            return states.Complete(source.amount_debited, source_id=source.pk)

    def create_actual_refund_with_gateway(self, source: Source, amount):
        # amount = int(amount * 100)
        client = self.client
        reference = source.reference or self.get_reference_from_source(source)
        payment_pgr = PaymentGateWayResponse.objects.filter(source=source).first()
        if not reference:
            reference = payment_pgr.response and payment_pgr.response.get('payment', {}).get('razor_pay', {}).get('razorpay_payment_id', '')
        if not reference:
            msg = 'Transaction Reference not found for razorpay payment.'
            print(msg)
            raise Exception(msg)
        order = source.order

        # EXTERNAL PAYMENT
        payment_response = client.payment.fetch(reference, str(amount))
        if payment_response['refund_status'] not in [None, 'partial']:
            return {'response': 'The referred amount could not be processed because, '
                                'remaining amount to be refunded is less than mentioned amount.'}
        payment_pgr.response = payment_response
        max_refundable_amount = payment_response['amount'] - payment_response['amount_refunded']
        if amount > max_refundable_amount:
            msg = f"""The Amount {source.currency} {amount}/- is more than the 
                    {source.currency} {max_refundable_amount} /-.  
                    The total amount of this order #{order.number} is 
                    {source.currency}  {payment_response['amount'] / 100}/-"""

            if payment_response['amount_refunded']:
                msg += f" and we already have refunded {source.currency} {payment_response['amount_refunded']/100} "
            msg += f""". In this situation, we could not proceed payment refund with the given amount. 
                    (Payment Reference : {reference}). """
            msg += f""" <br /> \nYou can copy / note down the reference number and go to razorpay dashboard 
                    to trigger a manual refund. """
            raise AlertException(msg)

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
            pgr.response = response
            pgr.transaction_id = response['id']

            # LOGGING RESPONSE
            pgr.payment_status = True
            pgr.save()
            return response

        except (
                razorpay.errors.BadRequestError,  # noqa
                razorpay.errors.ServerError, # noqa
                razorpay.errors.SignatureVerificationError, # noqa
                requests.exceptions.ConnectionError,
        ) as e:
            # payment Rejected Error
            pgr.payment_status = False
            pgr.response = {'id': reference, 'entity': 'payment', 'amount': amount, 'currency': source.currency,
                             'status': 'already_captured', 'error': str(e)}
            pgr.save()
            return {'id': reference, 'entity': 'payment', 'amount': amount, 'currency': source.currency,
                    'status': 'already_captured', 'error': str(e)}
            # return states.Declined(source.amount_debited, source_id=source.pk)



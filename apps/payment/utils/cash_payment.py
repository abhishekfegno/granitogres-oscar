from django.utils import timezone
from oscar.apps.payment.models import Source
from oscarapicheckout import states
from oscarapicheckout.methods import Transaction, PaymentMethod

from apps.payment.models import COD, PaymentGateWayResponse, CODRepayments
from apps.payment.utils import PaymentRefundMixin


class Cash(PaymentRefundMixin, PaymentMethod):
    """
    Accepts Cash on Delivery / Card on Delivery Payments overriding example payment from oscarapicheckout.
    """
    # Translators: Description of payment method in checkout
    name = 'Cash'
    code = 'cash'

    def _record_payment(self, request, order, method_key, amount, reference, **kwargs):
        source = self.get_source(order, reference)

        amount_to_allocate = amount - source.amount_allocated
        source.allocate(amount_to_allocate, reference)

        amount_to_debit = amount - source.amount_debited
        source.debit(amount_to_debit, reference)

        event = self.make_debit_event(order, amount_to_debit, reference)

        lines = kwargs.get('lines', order.lines.all())
        line_quantities = kwargs.get('line_quantities', [line.active_quantity for line in lines])
        for line, qty in zip(lines, line_quantities):
            self.make_event_quantity(event, line, qty)
        cod = COD.objects.create(
            order=source.order,
            amount=amount,
            created_on=timezone.now(),
            cod_accepted=False,
            cod_transferred=False,
            amount_received_on=None,
        )
        return states.Complete(source.amount_debited, source_id=source.pk)

    def create_actual_payment_with_gateway(self, source: Source, amount):
        """
        This method completely dedicated for refund procedure
        """
        cod = getattr(source.order, 'cod') if hasattr(source.order, 'cod') else None
        if not cod:
            cod = COD.objects.create(
                order=source.order,
                amount=source.order.total_incl_tax,
                created_on=timezone.now(),
                cod_accepted=False,
                cod_transferred=False,
                amount_received_on=None,
            )

        codr = CODRepayments()
        codr.cod = cod
        codr.amount = amount
        codr.save()

        pgr = PaymentGateWayResponse()
        pgr.order = source.order
        pgr.transaction_id = 'COD-0000-' + str(codr.id or 0)
        pgr.transaction_type = Transaction.REFUND
        pgr.source = source
        pgr.amount = amount
        pgr._response = codr.cod_response
        pgr.payment_status = True
        pgr.payee = source.order.user
        pgr.description = ''
        pgr.parent_transaction = None
        pgr.save()
        states.Complete(source.amount_debited, source_id=source.pk)
        return codr.cod_response

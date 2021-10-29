from django.utils import timezone
from apps.payment.models import Source
from oscarapicheckout import states
from oscarapicheckout.methods import Transaction, PaymentMethod, SourceType

from apps.payment.models import COD, PaymentGateWayResponse, CODRepayments
from apps.payment.utils import PaymentRefundMixin


class Cash(PaymentRefundMixin, PaymentMethod):
    """
    Accepts Cash on Delivery / Card on Delivery Payments overriding example payment from oscarapicheckout.
    """
    # Translators: Description of payment method in checkout
    name = 'Cash'
    code = 'cash'
    __source_type_obj = None

    @classmethod
    def as_source_type(cls):
        if cls.__source_type_obj is None:
            cls.__source_type_obj = SourceType.objects.get_or_create(name=cls.name, code=cls.code)[0]
        return cls.__source_type_obj

    def _record_payment(self, request, order, method_key, amount, reference, **kwargs):
        source = self.get_source(order, reference)

        self.allocate_payment(amount, source, reference)
        self.debit_payment(source)

        lines = kwargs.get('lines', order.lines.all())
        line_quantities = kwargs.get('line_quantities', [line.active_quantity for line in lines])
        # for line, qty in zip(lines, line_quantities):
        #     self.make_event_quantity(event, line, qty)
        cod = COD.objects.create(
            order=source.order,
            amount=amount,
            created_on=timezone.now(),
            cod_accepted=False,
            cod_transferred=False,
            amount_received_on=None,
        )
        # update system, that transaction is complete and we will somehow  internally manage remaining transactions.
        # these states are used for keeping in session by 'oscarapicheckout' package only.
        return states.Complete(source.amount_allocated, source_id=source.pk)

    def allocate_payment(self, amount, source, reference=''):
        amount_to_allocate = amount - source.amount_allocated
        source.allocate(amount_to_allocate, reference)

    def debit_payment(self, source, reference=''):
        amount_to_debit = source.amount_allocated - source.amount_debited
        source.debit(amount_to_debit, reference)
        event = self.make_debit_event(source.order, amount_to_debit, reference)
        order = source.order
        lines = order.lines.all()
        for line in lines:
            self.make_event_quantity(event, line, line.active_quantity)
        COD.objects.filter(order=source.order).update(cod_accepted=True)
        return states.Complete(source.amount_debited, source_id=source.pk)  # event

    def create_actual_refund_with_gateway(self, source: Source, amount):
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

        # !important
        codr = CODRepayments()      # Creating COD Response For Order Items.
        codr.cod = cod
        codr.amount = amount
        codr.save()

        # logging transaction
        pgr = PaymentGateWayResponse()
        pgr.order = source.order
        pgr.transaction_id = 'COD-0000-' + str(codr.id or 0)
        pgr.transaction_type = Transaction.REFUND
        pgr.source = source
        pgr.amount = amount
        pgr.response = codr.cod_response
        pgr.payment_status = True
        pgr.payee = source.order.user
        pgr.description = ''
        pgr.parent_transaction = None
        pgr.save()
        states.Complete(source.amount_debited, source_id=source.pk)
        return codr.cod_response

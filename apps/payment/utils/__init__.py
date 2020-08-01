from django.conf import settings
from django.db import models, transaction
from oscar.apps.order.models import Order, PaymentEvent, PaymentEventQuantity, LinePrice, Line
from oscar.apps.payment.models import Transaction, SourceType, Source


class PaymentRefundMixin(object):

    @transaction.atomic
    def __refund_amount_method(self, source: Source, amount: float, **kwargs):
        """
        General method for refunding.
        """
        order = source.order
        if not kwargs.get('amount_verified', False):        # handled internally
            amount = self.get_max_refundable_amount(source, amount_to_refund=amount)    # confirm for any external call

        # create actual payment
        response = self.create_actual_payment_with_gateway(
            source=source, amount=amount
        )
        assert type(response) is dict and 'id' in response.keys(), \
            "You have to return the response from gateway as dict with transaction_id as 'id'"

        # mark payment sources that we have refunded the money.
        source.refund(amount, source.reference)

        # create order transaction event object that we have refunded the money.
        event = self.make_refund_event(  # noqa
            order=order, amount=amount, reference=response['id']
        )

    def refund_order(self, order: Order, source: Source, **kwargs):
        """
        Refund the whole amount. There is a chance a product is already refunded.
        call from RefundFacade.refund_order
        """
        order = source.order
        refundable_amount = self.get_max_refundable_amount(source, amount_to_refund=None)
        self.__refund_amount_method(
            source=source,
            amount=float(refundable_amount),
            amount_verified=True,
        )
        for line in order.lines.all().exclude(status__in=settings.OSCAR_LINE_REFUNDABLE_STATUS):
            self.make_event_quantity(event, line, line.quantity)  # noqa
        return True

    def refund_order_line(self, line, source, quantity_to_refund: int, **kwargs):
        """
            Refund the whole amount for a product line.
            call from RefundFacade.refund_order_line
        """
        refundable_amount = self._qty_to_price(line, quantity_to_refund)

        refundable_amount = self.get_max_refundable_amount(source, refundable_amount)  # Net Amount
        self.__refund_amount_method(
            source=source,
            amount=float(refundable_amount),
            amount_verified=True,
        )
        # Creating Transaction For Payment
        self.make_event_quantity(event, line, line.quantity)  # noqa  # Creating PaymentEventQuantity For Order
        return True

    def refund_admin_defined_payment(self, order, event_type, amount,
                                     lines, line_quantities, source, **kwargs):
        """
            Refund the whole amount for a product line.
            call from RefundFacade.refund_order_line
        """
        refundable_amount = 0
        for line, qty in zip(lines, line_quantities):
            refundable_amount += line.line_price_incl_tax * qty / line.unit_price_incl_tax

        refundable_amount = self.get_max_refundable_amount(source, refundable_amount)  # Net Amount
        self.__refund_amount_method(
            source=source,
            amount=float(refundable_amount),
            amount_verified=True,
        )
        # # Creating Transaction For Payment
        # self.make_event_quantity(event, line, line.quantity)  #noqa  # Creating PaymentEventQuantity For Order
        # return event

    def get_max_refundable_amount(self, source: Source, amount_to_refund=None):
        """ Over ride this method, which is more proper from payment gateway. """
        if amount_to_refund is None:
            """ then considering, we have to refund the whole amount"""
            amount_to_refund = source.amount_debited - source.amount_refunded
        max_refundable_amount = source.amount_available_for_refund
        amount_to_refund = min(amount_to_refund, max_refundable_amount)
        return amount_to_refund

    def create_actual_payment_with_gateway(self, source: Source, amount: float):
        """ Override this module to trigger actual payment """
        reference = source.reference
        raise Exception("You have to override  'create_actual_payment_with_gateway' to act real world payment.")


    def _qty_to_price(self, line: Line, quantity_to_refund: int, **kwargs):
        """
            Refund specific quantity for a product line.
            # NB: some lines may be already refunded.
        """
        if quantity_to_refund is None:
            quantity_to_refund = line.quantity

        quantity_data = self._get_quantity_consumed(line)
        balance_quantity_in_line = quantity_data['debit']['quantity'] - quantity_data['refund']['quantity']
        quantity_to_refund = min(balance_quantity_in_line, quantity_to_refund)

        if quantity_to_refund == line.quantity:
            amount_to_refund = line.line_price_incl_tax
        else:
            amount_to_refund = quantity_to_refund * (line.line_price_incl_tax / line.unit_price_incl_tax)
        return amount_to_refund

    # def _get_refunded_line_quantity(self, line: Line):
    #     """ Returns no ogf events """
    #     out = line.payment_event_quantities.filter(
    #         models.Q(event__event_type__name=Transaction.REFUND)
    #     ).aggregate(refunded_quantity=models.Sum('quantity'))
    #     return out['refunded_quantity'] or 0

    def _get_quantity_consumed(self, order_line):
        order = order_line.order
        payment_event_quantities = PaymentEventQuantity.objects.filter(line=order_line, event__order=order) \
            .prefetch_related('event', 'event__event_type')
        refunded_quantity = 0
        refunded_amount = 0
        debited_quantity = 0
        debited_amount = 0
        for payment_event_qty in payment_event_quantities:
            if payment_event_qty.event.event_type.name == Transaction.DEBIT:
                debited_quantity += payment_event_qty.quantity
                debited_amount += payment_event_qty.event.amount
            if payment_event_qty.event.event_type.name == Transaction.REFUND:
                refunded_quantity += payment_event_qty.quantity
                refunded_amount += payment_event_qty.event.amount

        return {
            'debit': {
                'quantity': debited_quantity,
                'amount': debited_amount,
            },
            'refund': {
                'quantity': refunded_quantity,
                'amount': refunded_amount,
            }
        }

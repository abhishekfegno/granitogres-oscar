from django.conf import settings
from django.db import models
from oscar.apps.order.models import Order, PaymentEvent, PaymentEventQuantity, LinePrice
from oscar.apps.payment.models import Transaction


class PaymentRefundMixin(object):

    # def _calculate_max_refund_amount_for_order(self, order):
    #     return 0
    #
    # def _calculate_max_refund_amount_for_order_line(self, line):
    #     return 0

    def _get_refunded_order_lines(self, order_line):
        payment_events = order_line.order.payment_events.all()
        payment_event_quantities = PaymentEventQuantity.objects.filter(line=order_line)
        return 0

    def _get_quantity_consumed(self, order_line):
        order = order_line.order
        payment_event_quantities = PaymentEventQuantity.objects.filter(line=order_line, event__order=order)\
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

    def refund_order(self, order: Order, reference, **kwargs):
        """
        Refund the whole amount. There is a chance a product is already refunded before refunding the whole order.
        """
        source = self.get_source(order, reference)      # noqa

        amount_to_refund = min(source.amount_debted - source.amount_refunded, max_refundable_amount)  # re
        source.refund(amount_to_refund, reference)

        event = self.make_refund_event(order, amount_to_refund, reference)  # noqa
        for line in order.lines.all().exclude(status__in=settings.OSCAR_LINE_REFUNDABLE_STATUS): # noqa
            self.make_event_quantity(event, line, line.quantity)    # noqa

    def refund_order_line(self, line, reference, **kwargs):
        """
            Refund the whole amount for a product line.
        """
        source = self.get_source(order, reference)      # noqa
        max_refundable_amount = source.amount_available_for_refund       # Net Amount
        amount_to_refund = 0
        qty = 0
        for l in LinePrice.objects.filter(line=line):
            amount_to_refund += l.total_incl_tax + l.shipping_incl_tax
            qty += l.quantity
        amount_to_refund = min(amount_to_refund, max_refundable_amount)
        source.refund(amount_to_refund, reference)
        event = self.make_refund_event(order, amount_to_refund, reference)  # noqa
        self.make_event_quantity(event, line, line.quantity)    # noqa
        msg = f"Refunding #{line.id} with amount INR {amount_to_refund}/- against {qty} items."


from django.conf import settings
from django.db import models, transaction
from oscar.apps.order.models import Order, PaymentEvent, PaymentEventQuantity, LinePrice
from oscar.apps.payment.models import Transaction, SourceType, Source


class PaymentRefundMixin(object):

    def get_payment_event_quantity(self, line):
        return line.payment_event_quantities.filter(
            event__event_type__name=Transaction.REFUND
        ).aggregate(refunded_quantity=models.Sum('quantity'))['refunded_quantity'] or 0

    def get_source_or_none(self, order):
        return Source.objects.filter(order=order, source_type__name=self.name).first()

    @transaction.atomic
    def refund_order(self, order: Order, reference, **kwargs):
        """
        Refund the whole amount. There is a chance a product is already refunded.
        """
        source = self.get_source_or_none(order)      # noqa
        if not source or not source.amount_available_for_refund:
            return

        amount_to_refund = source.amount_debted - source.amount_refunded  # re
        max_refundable_amount = source.amount_available_for_refund
        amount_to_refund = min(amount_to_refund, max_refundable_amount)
        source.refund(amount_to_refund, reference)
        event = self.make_refund_event(order, amount_to_refund, reference)  # noqa
        for line in order.lines.all().exclude(status__in=settings.OSCAR_LINE_REFUNDABLE_STATUS): # noqa
            self.make_event_quantity(event, line, line.quantity)    # noqa

    @transaction.atomic
    def refund_order_line(self, line, reference, **kwargs):
        """
            Refund the whole amount for a product line.
        """

        source = self.get_source_or_none(order=line.order)      # noqa
        if not source or not source.amount_available_for_refund:
            return

        max_refundable_amount = source.amount_available_for_refund       # Net Amount
        order = line.order
        amount_to_be_refunded = line.line_price_incl_tax
        refundable_amount = min(amount_to_be_refunded, max_refundable_amount)
        reference = reference[-127:]
        import pdb
        pdb.set_trace()

        source.refund(refundable_amount, reference)

        event = self.make_refund_event(order=order, amount=refundable_amount, reference=reference)
                                                                            # Creating Transaction For Payment
        self.make_event_quantity(event, line, line.quantity)                # noqa  # Creating PaymentEventQuantity For Order

    @transaction.atomic
    def refund_order_line_for_specific_quantity(self, line, quantity_to_refund, reference, **kwargs):
        """
            Refund specific quantity for a product line.
        """

        source = self.get_source_or_none(order)      # noqa
        if not source and not source.amount_available_for_refund:
            return source

        max_refundable_amount = source.amount_available_for_refund       # Net Amount

        amount_to_be_refunded = line.line_price_incl_tax * quantity_to_refund / line.quantity
        refundable_amount = min(amount_to_be_refunded, max_refundable_amount)
        quantity_remaining_to_refund = line.quantity - quantity_to_refund - self.get_payment_event_quantity(line)
        if int(refundable_amount) == 0:
            return

        msg = f"Refunding #{line.id} with amount INR {refundable_amount}/- against {quantity_to_refund} items " \
              f"(remaining {quantity_remaining_to_refund})."
        reference = reference or msg

        source.refund(refundable_amount, reference)
        event = self.make_refund_event(order=line.order, amount=refundable_amount, reference=reference)  # Creating Transaction For Payment
        self.make_event_quantity(event, line, line.quantity)                # noqa  # Creating PaymentEventQuantity For Order


    # def _calculate_max_refund_amount_for_order(self, order):
    #     return 0
    #
    # def _calculate_max_refund_amount_for_order_line(self, line):
    #     return 0

    # def _get_refunded_order_lines(self, order_line):
    #     payment_events = order_line.order.payment_events.all()
    #     payment_event_quantities = PaymentEventQuantity.objects.filter(line=order_line)
    #     return 0

    # def _get_quantity_consumed(self, order_line):
    #     order = order_line.order
    #     payment_event_quantities = PaymentEventQuantity.objects.filter(line=order_line, event__order=order)\
    #         .prefetch_related('event', 'event__event_type')
    #     refunded_quantity = 0
    #     refunded_amount = 0
    #     debited_quantity = 0
    #     debited_amount = 0
    #     for payment_event_qty in payment_event_quantities:
    #         if payment_event_qty.event.event_type.name == Transaction.DEBIT:
    #             debited_quantity += payment_event_qty.quantity
    #             debited_amount += payment_event_qty.event.amount
    #         if payment_event_qty.event.event_type.name == Transaction.REFUND:
    #             refunded_quantity += payment_event_qty.quantity
    #             refunded_amount += payment_event_qty.event.amount
    #
    #     return {
    #         'debit': {
    #             'quantity': debited_quantity,
    #             'amount': debited_amount,
    #         },
    #         'refund': {
    #             'quantity': refunded_quantity,
    #             'amount': refunded_amount,
    #         }
    #     }

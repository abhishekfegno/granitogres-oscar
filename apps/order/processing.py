from typing import Any

from django.conf import settings
from django.db import models, transaction
from oscar.apps.order import processing
from oscar.core.loading import get_model

from .models import Order, PaymentEventType
from ..payment import refunds
from ..payment.refunds import RefundFacade
from ..payment.utils.cash_payment import Cash

Transaction = get_model('payment', 'Transaction')


class EventHandler(processing.EventHandler):

    @transaction.atomic
    def handle_order_status_change(self, order: Order, new_status: str, note_msg=None):
        """
        Handle Order Status Change in Oscar.
        """

        """
        Change Order Status
        """
        old_status = order.status
        order.set_status(new_status)

        """ 
        Handle Refund and Update of Refund Quantity on `new_status` == 'Return'. 
        Refund Can be proceeded only after changing Order Status.
        """

        if new_status in settings.OSCAR_ORDER_REFUNDABLE_STATUS:
            refunds.RefundFacade().refund_order(order=order)
            order.lines.update(refunded_quantity=models.F('quantity'))

        if new_status in (settings.ORDER_STATUS_DELIVERED, ):
            """
            Update Order Lines Status  as Delivered along with Order Getting Delivered.
            """
            order.lines.exclude(
                status__in=settings.OSCAR_LINE_REFUNDABLE_STATUS
            ).update(status=new_status)


        if note_msg:
            """
            Add note if there is a note msg.
            """
            self.create_note(order, note_msg)

    def handle_payment_event(self, order, event_type: PaymentEventType, amount, lines=None,
                             line_quantities=None, **kwargs):
        """
        Handle a payment event for a given order.

        These should normally be called as part of handling a shipping event.
        It is rare to call to this method directly.  It does make sense for
        refunds though where the payment event may be unrelated to a particular
        shipping event and doesn't directly correspond to a set of lines.
        """
        self.validate_payment_event(
            order, event_type, amount, lines, line_quantities, **kwargs)

        if event_type.name == Transaction.DEBIT:
            Cash().record_payment(request=None, order=order, method_key='cash', amount=amount, reference='',
                                  lines=lines, line_quantities=line_quantities, **kwargs)

        # if event_type.name == Transaction.REFUND:
        #     RefundFacade().refund_admin_defined_payment(
        #         order, event_type, amount, lines=lines, line_quantities=line_quantities, **kwargs
        #     )

        return self.create_payment_event(
            order, event_type, amount, lines, line_quantities, **kwargs)

    @transaction.atomic
    def handle_order_line_status_change(self, order_line, new_status: str, note_msg=None):
        """
        Handle Order Status Change in Oscar.
        """

        """
        Change Order Status
        """
        old_status = order_line.status
        order_line.set_status(new_status)

        """ 
        Handle Refund and Update of Refund Quantity on `new_status` == 'Return'. 
        Refund Can be proceeded only after changing Order Status.
        """
        if new_status in settings.OSCAR_LINE_REFUNDABLE_STATUS:
            refunds.RefundFacade().refund_order_line(line=order_line)
            order_line.refunded_quantity = order_line.quantity
            order_line.save()
        if note_msg:
            """
            Add note if there is a note msg.
            """
            self.create_note(order_line.order, note_msg)




from oscar.apps.order import processing
from .models import Order, PaymentEventType
from ..payment.refunds import RefundFacade


class EventHandler(processing.EventHandler):

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
        if event_type.name == 'Refund':
            RefundFacade().refund_admin_defined_payment(
                order, event_type, amount, lines=None, line_quantities=None, **kwargs
            )
        return self.create_payment_event(
            order, event_type, amount, lines, line_quantities, **kwargs)






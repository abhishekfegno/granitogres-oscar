from oscar.apps.order import processing
from .refunding import FundTransfer
from .models import Order


class EventHandler(processing.EventHandler):

    def handle_order_status_change(self, order: Order, new_status: str, note_msg=None):
        """
        Handle a requested order status change

        This method is not normally called directly by client code.  The main
        use-case is when an order is cancelled, which in some ways could be
        viewed as a shipping event affecting all lines.
        """
        print("order status is changing: ", order.status, " => ", new_status)

        order.set_status(new_status)
        if note_msg:
            self.create_note(order, note_msg)

from oscar.apps.order import processing
from .models import Order


class EventHandler(processing.EventHandler):

    def handle_order_status_change(self, order: Order, new_status: str, note_msg=None):
        """
        Handle a requested order status change

        This method is not normally called directly by client code.  The main
        use-case is when an order is cancelled, which in some ways could be
        viewed as a shipping event affecting all lines.
        """

        old_status = order.status

        if new_status in order.available_statuses():
            print("order status is changing: ", old_status, " => ", new_status)
            # running 'apps.order.signal_receivers.order_status_changed__receiver'
        order.set_status(new_status)
        if note_msg:
            self.create_note(order, note_msg)

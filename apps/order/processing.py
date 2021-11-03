from typing import Any

from django.conf import settings
from django.db import models, transaction
from django.utils.module_loading import import_string
from oscar.apps.checkout.mixins import OrderPlacementMixin
from oscar.apps.customer.alerts.utils import Dispatcher
from oscar.apps.order import processing
from apps.payment.models import SourceType
from oscar.core.loading import get_model

from .models import Order, PaymentEventType
from ..payment import refunds
from ..payment.refunds import RefundFacade
from ..payment.utils.cash_payment import Cash
from ..utils.email_notifications import EmailNotification
from ..utils.pushnotifications import OrderStatusPushNotification, PushNotification
from ..utils.utils import get_statuses

Transaction = get_model('payment', 'Transaction')
Line = get_model('order', 'Line')


class EventHandler(processing.EventHandler):

    @staticmethod
    def pipeline_order_lines(order, new_status):
        if new_status in get_statuses(1+2+4+8):
            order.lines.exclude(
                status__in=settings.OSCAR_LINE_REFUNDABLE_STATUS
            ).update(status=new_status)
        return

    @transaction.atomic
    def handle_order_status_change(self, order: Order, new_status: str, note_msg=None, note_type='System'):
        """
        Handle Order Status Change in Oscar.
        """

        """
        Change Order Status
        """
        old_status = order.status
        order.set_status(new_status)
        OrderStatusPushNotification(order.user).send_status_update(order, new_status)

        """ 
        Handle Refund and Update of Refund Quantity on `new_status` == 'Return'. 
        Refund Can be proceeded only after changing Order Status.
        """
        if (
                old_status not in settings.OSCAR_ORDER_REFUNDABLE_STATUS
                and
                new_status in settings.OSCAR_ORDER_REFUNDABLE_STATUS
        ):
            refunds.RefundFacade().refund_order(order=order)
            order.lines.update(refunded_quantity=models.F('quantity'))
        self.pipeline_order_lines(order, new_status)

        all_lines = order.lines.all().select_related('stockrecord')
        if new_status in get_statuses(8):
            lines_to_be_consumed = all_lines.filter(status__in=get_statuses(8))
            self.consume_stock_allocations(order, lines_to_be_consumed)
        elif new_status in get_statuses(128):
            lines_to_be_cancelled = all_lines.filter(status__in=get_statuses(128))
            self.cancel_stock_allocations(order, lines_to_be_cancelled)

        if new_status in settings.OSCAR_SEND_EMAIL_ORDER_STATUS:
            """
            documentatiomn: how we process the logic.
            concidering the order status ; we create a code such that
            
            order__placed for "Placed Status", order__order_confirmed for "Order Confirmed" Status etc...
            we need to place 
            * 'templates/oscar/customer/emails/commtype_<order_code>_subject.txt'
            * 'templates/oscar/customer/emails/commtype_<order_code>_subject.txt'
            * 'templates/oscar/customer/emails/commtype_<order_code>_body.html'
            * 'templates/oscar/customer/sms/commtype_<order_code>_body.txt'
            
            files for each status to work with this logic.
            """
            order_code = f"order__{new_status.lower().replace(' ', '_')}"
            opm = OrderPlacementMixin()

            class FakeReq:
                user = order.user

            opm.request = FakeReq()
            # opm.send_confirmation_message(order, order_code)
            print(order, order_code)
            print(opm.get_message_context(order, order_code))
            # print(opm.send_confirmation_message(order, order_code))


        if hasattr(order, 'consignmentdelivery'):
            if new_status == settings.ORDER_STATUS_DELIVERED:
                order.consignmentdelivery.status = order.consignmentdelivery.COMPLETED
                order.consignmentdelivery.save()
                if (
                        order.consignmentdelivery.delivery_trip
                        and order.consignmentdelivery.delivery_trip.status == order.consignmentdelivery.delivery_trip.ON_TRIP
                ):
                    PushNotification(order.consignmentdelivery.delivery_trip.agent).send_message(
                        title=f"Consignment #handler{order.consignmentdelivery.id} has been Delivered!",
                        message="Hey, a delivery consignment has been marked as Delivered! Moving items to completed "
                                "list!",
                    )
            elif new_status == settings.ORDER_STATUS_CANCELED:
                order.consignmentdelivery.status = order.consignmentdelivery.CANCELLED
                order.consignmentdelivery.save()
                if (
                        order.consignmentdelivery.delivery_trip
                        and order.consignmentdelivery.delivery_trip.status == order.consignmentdelivery.delivery_trip.ON_TRIP
                ):
                    PushNotification(order.consignmentdelivery.delivery_trip.agent).send_message(
                        title=f"Consignment #{order.consignmentdelivery.id} has been Cancelled!",
                        message="Hey, a delivery consignment has been marked as Cancelled! Moving items to cancelled "
                                "list!",
                    )

        if hasattr(order, 'consignmentreturn'):
            if new_status == settings.ORDER_STATUS_RETURN_APPROVED:
                order.consignmentreturn.status = order.consignmentreturn.COMPLETED
                order.consignmentreturn.save()
                if (
                        order.consignmentreturn.delivery_trip
                        and order.consignmentreturn.delivery_trip.status == order.consignmentreturn.delivery_trip.ON_TRIP
                ):
                    PushNotification(order.consignmentreturn.delivery_trip.agent).send_message(
                        title=f"Return #{order.consignmentreturn.id} has been Picked Up!",
                        message="Hey, A return consignment has been marked as Picked Up! Moving items to completed "
                                "list!",
                    )
            elif old_status in get_statuses(32+16) and new_status == settings.ORDER_STATUS_DELIVERED:
                order.consignmentreturn.status = order.consignmentreturn.CANCELLED
                order.consignmentreturn.save()
                if (
                        order.consignmentreturn.delivery_trip
                        and (
                        order.consignmentreturn.delivery_trip.status
                        == order.consignmentreturn.delivery_trip.ON_TRIP
                )):
                    PushNotification(order.consignmentreturn.delivery_trip.agent).send_message(
                        title=f"Return #{order.consignmentreturn.id} has been Cancelled!",
                        message="Hey, a return consignment has been marked as Cancelled! Moving items to cancelled "
                                "list!",
                    )

            elif new_status == settings.ORDER_STATUS_OUT_FOR_DELIVERY:
                pass

        if note_msg:
            """
            Add note if there is an EventHandler note msg.
            """
            self.create_note(order, note_msg, note_type=note_type)

    def handle_payment_event(self, order, event_type: PaymentEventType, amount, lines=None,
                             line_quantities=None, **kwargs):
        """
        Handle a payment event for a given order.

        These should normally be called as part of handling a shipping event.
        It is rare to call to this method directly.  It does make sense for
        refunds though where the payment event may be unrelated to a particular
        shipping event and doesn't directly correspond to a set of lines.
        """
        OrderStatusPushNotification(order.user).send_refund_update(order, amount)

        self.validate_payment_event(
            order, event_type, amount, lines, line_quantities, **kwargs)

        # if event_type.name == Transaction.DEBIT:
        #     Cash().record_payment(request=None, order=order, method_key='cash', amount=amount, reference='',
        #                           lines=lines, line_quantities=line_quantities, **kwargs)
        #
        # if event_type.name == Transaction.REFUND:
        #     RefundFacade().refund_admin_defined_payment(
        #         order, event_type, amount, lines=lines, line_quantities=line_quantities, **kwargs
        #     )

        return self.create_payment_event(
            order, event_type, amount, lines, line_quantities, **kwargs)

    @transaction.atomic
    def handle_order_line_status_change(
            self, order_line, new_status: str, note_msg=None, note_type='System', already_refunded_together=False):
        """
        Handle Order Status Change in Oscar.
        """

        """
        Change Order Status
        """
        old_status = order_line.status
        if old_status == new_status:
            return
        order = order_line.order
        order_line.set_status(new_status)

        """ 
        Handle Refund and Update of Refund Quantity on `new_status` == 'Return'. 
        Refund Can be proceeded only after changing Order Status.
        """
        if not already_refunded_together:
            if new_status in settings.OSCAR_LINE_REFUNDABLE_STATUS:
                refunds.RefundFacade().refund_order_line(line=order_line)
                order_line.refunded_quantity = order_line.quantity
                order_line.save()
        if new_status in get_statuses(64+32+16):  # any status from processing requests
            order.set_status(new_status)

        if new_status in get_statuses(8):
            self.consume_stock_allocations(order, [order_line])
        elif new_status in get_statuses(128):
            self.cancel_stock_allocations(order, [order_line])

        if note_msg:
            """
            Add note if there is an EventHandler note msg.
            """
            self.create_note(order, message=note_msg, note_type=note_type)

    def consume_stock_allocations(self, order, lines=None, line_quantities=None):
        """
        Consume the stock allocations for the passed lines.

        If no lines/quantities are passed, do it for all lines.
        """
        if not lines:
            lines = order.lines.all()
        if not line_quantities:
            line_quantities = [line.quantity for line in lines]
        for line, qty in zip(lines, line_quantities):
            if line.stockrecord:
                line.stockrecord.consume_allocation(qty)

    def cancel_stock_allocations(self, order, lines=None, line_quantities=None):
        """
        Cancel the stock allocations for the passed lines.

        If no lines/quantities are passed, do it for all lines.
        """
        if not lines:
            lines = order.lines.all()
        if not line_quantities:
            line_quantities = [line.quantity for line in lines]
        for line, qty in zip(lines, line_quantities):
            if line.stockrecord:
                line.stockrecord.cancel_allocation(qty)


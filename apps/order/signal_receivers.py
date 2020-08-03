from django.conf import settings
from django.db import models
from django.dispatch import receiver
from django.utils.module_loading import import_string
from oscar.apps.order.signals import order_line_status_changed, order_status_changed

from apps.payment import refunds


@receiver(order_status_changed)
def order_status_changed__receiver(order, old_status, new_status, **kwargs):
    """ Make line status "Delivered" on  Order become "Delivered" """

    """
    Pay refund related things in EventHandler
    """


@receiver(order_line_status_changed)
def order_line_status_changed__receiver_for_refund(line, old_status, new_status, **kwargs):

    if new_status in settings.OSCAR_LINE_REFUNDABLE_STATUS:
        refunds.RefundFacade().refund_order_line(order=line.order, line=line)
        line.refunded_quantity = line.quantity
        line.save()











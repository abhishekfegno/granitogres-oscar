from django.conf import settings
from django.db import models
from django.dispatch import receiver
from django.utils.module_loading import import_string
from oscar.apps.order.signals import order_line_status_changed, order_status_changed

from apps.payment import refunds


@receiver(order_status_changed)
def order_status_changed__receiver(order, old_status, new_status, **kwargs):
    """ Make line status "Delivered" on  Order become "Delivered" """
    if old_status != new_status and new_status == settings.ORDER_STATUS_DELIVERED:
        order.lines.exclude(
            status__in=settings.OSCAR_LINE_REFUNDABLE_STATUS
        ).update(status=settings.ORDER_STATUS_DELIVERED)

    if any([
        old_status == new_status,
        old_status in settings.OSCAR_LINE_REFUNDABLE_STATUS,
        new_status not in settings.OSCAR_LINE_REFUNDABLE_STATUS,
    ]):
        return None
    refunds.RefundFacade().refund_order(order=order)

    if new_status == settings.ORDER_STATUS_RETURNED:
        order.lines.update(refunded_quantity=models.F('quantity'))


@receiver(order_line_status_changed)
def order_line_status_changed__receiver(line, old_status, new_status, **kwargs):
    if any([
        old_status == new_status,
        old_status in settings.OSCAR_LINE_REFUNDABLE_STATUS,
        new_status not in settings.OSCAR_LINE_REFUNDABLE_STATUS,
    ]):
        return None
    refunds.RefundFacade().refund_order_line(order=line.order, line=line)

    if new_status == settings.ORDER_STATUS_RETURNED:
        line.refunded_quantity = line.quantity
        line.save()











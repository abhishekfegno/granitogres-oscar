from django.conf import settings
from django.dispatch import receiver
from django.utils.module_loading import import_string
from oscar.apps.order.signals import order_line_status_changed, order_status_changed

from apps.payment import refunds


@receiver(order_status_changed)
def order_status_changed__receiver(order, old_status, new_status, **kwargs):
    if any([
        old_status == new_status,
        old_status in settings.OSCAR_LINE_REFUNDABLE_STATUS,
        new_status not in settings.OSCAR_LINE_REFUNDABLE_STATUS,
    ]):
        return None
    refunds.RefundFacade().refund_order(order=order)


@receiver(order_line_status_changed)
def order_line_status_changed__receiver(line, old_status, new_status, **kwargs):
    if any([
        old_status == new_status,
        old_status in settings.OSCAR_LINE_REFUNDABLE_STATUS,
        new_status not in settings.OSCAR_LINE_REFUNDABLE_STATUS,
    ]):
        return None
    refunds.RefundFacade().refund_order_line(order=line.order, line=line)











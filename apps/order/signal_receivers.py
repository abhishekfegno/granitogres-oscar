from django.conf import settings
from django.dispatch import receiver
from oscar.apps.order.signals import order_line_status_changed


@receiver(order_line_status_changed)
def order_status_changed__receiver(line, old_status, new_status, **kwargs):
    if any([
        old_status == new_status,
        old_status in settings.OSCAR_LINE_REFUNDABLE_STATUS,
        new_status not in settings.OSCAR_LINE_REFUNDABLE_STATUS,
    ]):
        return None











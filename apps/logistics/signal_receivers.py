from django.dispatch import receiver
from oscar.apps.order.signals import order_line_status_changed, order_status_changed

from apps.logistics import settings
from apps.logistics.models import ConsignmentDelivery, ConsignmentReturn


@receiver(order_status_changed)
def order_status_changed__receiver_for_consignment_return(order, old_status, new_status, **kwargs):
    if new_status == settings.LOGISTICS_CONSIGNMENT_CREATE_STATUS_FOR_ORDER:
        cd, created = ConsignmentDelivery.objects.get_or_create(order=order)


@receiver(order_line_status_changed)
def order_line_status_changed__receiver_for_consignment_items_return(line, old_status, new_status, **kwargs):
    """
    Cases:
        1. Someone triggered a "Return Initiate" Request" against an  order.
            (Should create new  ConsignmentReturn)
        2. While delivery boy is on the way, someone cancelled 'Return Request'
            (Should update existing ConsignmentReturn)
        3. Customer again triggered a "Return initiate" after cancelling "Return Initiative"
            but before delivery boy mark it as completed.
            (Should update existing ConsignmentReturn)
        4. Customer again triggered a "Return initiate" after cancelling "Return Initiative"
            but after delivery boy mark it as completed.
            (Should create new ConsignmentReturn)
    """

    if new_status == settings.LOGISTICS_CONSIGNMENT_CREATE_STATUS_FOR_ORDER_LINE_RETURN:
        """ 
        Order line triggered "Return Initiated" 
        Handle Cases 1 3 & 4.
        """
        cr = ConsignmentReturn.generate(line)

    if (
            old_status == settings.LOGISTICS_CONSIGNMENT_CREATE_STATUS_FOR_ORDER_LINE_RETURN and
            new_status == settings.LOGISTICS_CONSIGNMENT_DESTROY_STATUS_FOR_ORDER_LINE_RETURN_CANCELLED
    ):
        """ 
        Handle Case 2 
        """
        ConsignmentReturn.cancel_consignment(line)




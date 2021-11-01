from django.conf import settings
from django.dispatch import receiver
from django.utils.datetime_safe import datetime
from oscar.apps.dashboard.communications.views import Dispatcher
from oscar.apps.order.signals import order_line_status_changed, order_status_changed
from apps.order.models import Order
from apps.payment import refunds


@receiver(order_status_changed)
def order_status_changed__receiver(order, old_status, new_status, **kwargs):
    """ Make line status "Delivered" on  Order become "Delivered" """
    if new_status == settings.ORDER_STATUS_DELIVERED:
        Order.objects.filter(pk=order.pk).update(date_delivered=datetime.now())
        order = Order.objects.filter(pk=order.pk)
        email = order.email

        dispatch = Dispatcher()
        order = {
            'orderID': order.id,
            'shipping_address': order.shipping_address,
            'date_of_order': order.date_placed,
            'products': {i.id: {'image': i.product.primary_image(),
                                'name': i.product.name,
                                'quantity': i.quantity,
                                'price': i.product.effective_price,
                                'total': i.line_price_incl_tax,
                                } for i in order.lines.all()},
            'total': order.total_incl_tax,
        }
        msgs = order
        dispatch.send_email_messages(email, msgs)


@receiver(order_line_status_changed)
def order_line_status_changed__receiver_for_refund(line, old_status, new_status, **kwargs):
    pass
    # if new_status in settings.OSCAR_LINE_REFUNDABLE_STATUS:
    #     refunds.RefundFacade().refund_order_line(order=line.order, line=line)
    #     line.refunded_quantity = line.quantity
    #     line.save()











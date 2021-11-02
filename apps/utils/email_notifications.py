from django.conf import settings
from django.core.mail import EmailMultiAlternatives, EmailMessage
from oscar.apps.customer.models import Email
from oscar.core import logging

from apps.order.models import CommunicationEvent


class EmailNotification:

    USER_TYPE = (settings.CUSTOMER, settings.DELIVERY_BOY, )

    def get_mail_format(self, order):
        data = {
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
        msgs = data
        email = order.email
        return email, msgs


OSCAR_ORDER_STATUS_CHANGE_MESSAGE = {
    settings.ORDER_STATUS_PLACED: {
        'title': 'Your order has been placed! Please Refer #{order.number} for more details.',
        'message': 'You have ordered {", ".join([i.product_title for i in order.lines.all()[:3]])}. ',
    },
    settings.ORDER_STATUS_CONFIRMED: {
        'title': 'We are Preparing your Basket! Please Refer #{order.number} for more details.',
        'message': 'Order Confirmed! Please Refer #{order.number} for more details. Tap to open',
    },
    settings.ORDER_STATUS_OUT_FOR_DELIVERY: {
        'title': 'On the Way to delivery with #{order.number}! Please Refer #{order.number} for more details.',
        'message': 'We might reach you within a couple of hours! Tap to open',
    },
    settings.ORDER_STATUS_DELIVERED: {
        'title': 'Your Order #{order.number} has been delivered! ',
        'message': 'We might reach you within a couple of hours! Tap to open',
    },
    settings.ORDER_STATUS_RETURN_REQUESTED: {
        'title': 'Your Return Request for some items has been forwarded!',
        'message': '#{order.number}! {", ".join([i.product_title for i in order.lines.filter(status="Return Requested")])}',
    },
    settings.ORDER_STATUS_RETURN_APPROVED: {
        'title': 'Your Return Request has been Approved!',
        'message': '#{order.number}! {", ".join([i.product_title for i in order.lines.filter(status="Return Approved")])}',
    },
    settings.ORDER_STATUS_RETURNED: {
        'title': 'Return Completed! Payment has been processed! ',
        'message': 'Return request against #{order.number} has been completed! Payment will be into your account '
                   'withn 2-7 working days Tap to open',
    },
    settings.ORDER_STATUS_CANCELED: {
        'title': 'Your Order #{order.number} Has Been Cancelled!!',
        'message': 'Please Check your orders for more details! #{order.number}! ',
    },
    settings.ORDER_STATUS_PAYMENT_DECLINED: {
        'title': 'Payment Has Been Declined! Order #{order.number}!',
        'message': 'Please Check your orders for more details! #{order.number}! ',
    },
}



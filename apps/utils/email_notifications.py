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

class Dispatcher(object):
    def __init__(self, logger=None, mail_connection=None):
        if not logger:
            logger = logging.getLogger(__name__)
        self.logger = logger
        # Supply a mail_connection if you want the dispatcher to use that
        # instead of opening a new one.
        self.mail_connection = mail_connection

    # Public API methods

    def dispatch_direct_messages(self, recipient, messages):
        """
        Dispatch one-off messages to explicitly specified recipient.
        """
        if messages['subject'] and (messages['body'] or messages['html']):
            return self.send_email_messages(recipient, messages)

    def dispatch_order_messages(self, order, messages, event_type=None, **kwargs):
        """
        Dispatch order-related messages to the customer.
        """
        if order.is_anonymous:
            email = kwargs.get('email_address', order.guest_email)
            dispatched_messages = self.dispatch_anonymous_messages(email, messages)
        else:
            dispatched_messages = self.dispatch_user_messages(order.user, messages)

        self.create_communication_event(order, event_type, dispatched_messages)

    def dispatch_anonymous_messages(self, email, messages):
        dispatched_messages = {}
        if email:
            dispatched_messages['email'] = self.send_email_messages(email, messages), None
        return dispatched_messages

    def dispatch_user_messages(self, user, messages):
        """
        Send messages to a site user
        """
        dispatched_messages = {}
        if messages['subject'] and (messages['body'] or messages['html']):
            dispatched_messages['email'] = self.send_user_email_messages(user, messages)
        if messages['sms']:
            dispatched_messages['sms'] = self.send_text_message(user, messages['sms'])
        return dispatched_messages

    # Internal

    def create_communication_event(self, order, event_type, dispatched_messages):
        """
        Create order communications event for audit
        """
        if dispatched_messages and event_type is not None:
            CommunicationEvent._default_manager.create(order=order, event_type=event_type)

    def create_customer_email(self, user, messages, email):
        """
        Create Email instance in database for logging purposes.
        """
        # Is user is signed in, record the event for audit
        if email and user.is_authenticated:
            return Email._default_manager.create(user=user,
                                                 email=user.email,
                                                 subject=email.subject,
                                                 body_text=email.body,
                                                 body_html=messages['html'])

    def send_user_email_messages(self, user, messages):
        """
        Send message to the registered user / customer and collect data in database.
        """
        if not user.email:
            self.logger.warning("Unable to send email messages as user #%d has"
                                " no email address", user.id)
            return None, None

        email = self.send_email_messages(user.email, messages)
        return email, self.create_customer_email(user, messages, email)

    def send_email_messages(self, recipient, messages):
        """
        Send email to recipient, HTML attachment optional.
        """
        if hasattr(settings, 'OSCAR_FROM_EMAIL'):
            from_email = settings.OSCAR_FROM_EMAIL
        else:
            from_email = None

        # Determine whether we are sending a HTML version too
        if messages['html']:
            email = EmailMultiAlternatives(messages['subject'],
                                           messages['body'],
                                           from_email=from_email,
                                           to=[recipient])
            email.attach_alternative(messages['html'], "text/html")
        else:
            email = EmailMessage(messages['subject'],
                                 messages['body'],
                                 from_email=from_email,
                                 to=[recipient])
        self.logger.info("Sending email to %s" % recipient)

        if self.mail_connection:
            self.mail_connection.send_messages([email])
        else:
            email.send()

        return email
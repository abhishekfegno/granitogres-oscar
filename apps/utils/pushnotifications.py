import logging
import os
from pprint import pprint
from typing import Optional

from django.conf import settings
from push_notifications.models import GCMDevice, APNSDevice, APNSDeviceQuerySet, GCMDeviceQuerySet
from pyfcm import FCMNotification

from apps.order.models import Order
logger = logging.getLogger(__name__)


class MessageProtocol:
    title = None
    message = None
    action = None
    icon = None

    def __init__(self, title, message, action, icon=None, **kwargs):
        self.title = title
        self.message = message
        self.action = action
        self.icon = icon
        self.kwargs = kwargs

    def as_dict(self):
        """
        payload can have
            message_body=None,
            message_title=None,
            message_icon=None,
            sound=None,
            condition=None,
            collapse_key=None,
            delay_while_idle=False,
            time_to_live=None,
            restricted_package_name=None,
            low_priority=False,
            dry_run=False,
            data_message=None,
            click_action=None,
            badge=None,
            color=None,
            tag=None,
            body_loc_key=None,
            body_loc_args=None,
            title_loc_key=None,
            title_loc_args=None,
            content_available=None,
            android_channel_id=None,
            timeout=5,
            extra_notification_kwargs=None,
            extra_kwargs={}
        """
        return {
            "message_title": self.title, "message_body": self.message + "\nTap to View More!",
            'click_action': self.action, 'message_icon': self.icon,
            **self.kwargs
        }


class PushNotification:
    """
    Instead od django-push-notification, we are using pyfcm to send message to server!
    since we have got some authentication issue with the package!
    """
    USER_TYPE = (settings.CUSTOMER, settings.DELIVERY_BOY, )

    def __init__(self, *users):
        self.fcm_devices: GCMDeviceQuerySet = GCMDevice.objects.filter(user__in=users) or None
        self.apn_devices: APNSDeviceQuerySet = APNSDevice.objects.filter(user__in=users) or None

    def get_apn_ids(self):
        out = []
        if self.USER_TYPE is not None:
            for app_id in settings.PUSH_DEVICES:
                if settings.PUSH_DEVICES[app_id] == self.USER_TYPE:
                    out.append(app_id)
        return out

    def fcm_send_message(self, queryset, message, **kwargs):
        response = []
        cloud_type = "FCM"
        data = kwargs.pop("extra", {})

        if message is not None:
            data["message"] = message

        # app_ids = queryset.filter(
        #     active=True,
        # ).order_by("application_id").values_list("application_id", flat=True).distinct()

        for app_id in self.get_apn_ids():

            registration_ids = list(queryset.filter(
                active=True, cloud_message_type=cloud_type, application_id=app_id
            ).values_list("registration_id", flat=True))

            if registration_ids:
                try:
                    push_service = FCMNotification(
                        api_key=settings.PUSH_NOTIFICATIONS_SETTINGS['APPLICATIONS'][app_id]['API_KEY'])
                    result = push_service.notify_multiple_devices(
                        registration_ids=registration_ids,
                        **kwargs
                    )
                    response.append(result)
                except Exception as e:
                    print(e)
                    logger.error(e)
                    raise e
        return response

    def apn_send_message(self, queryset, message, **kwargs):
        # TRY DOC https://pypi.org/project/pyapns-client/
        data = kwargs.pop("extra", {})
        if message is not None:
            data["message"] = message
        # app_ids = queryset.filter(
        #     active=True
        # ).order_by("application_id").values_list("application_id", flat=True).distinct()
        response = []
        cloud_type = "FCM"
        for app_id in self.get_apn_ids():
            registration_ids = list(queryset.filter(
                active=True, cloud_message_type=cloud_type, application_id=app_id
            ).values_list("registration_id", flat=True))

            if registration_ids:
                push_service = """  GET A PUSH NOTIFICATION OBJECT  HERE """
                raise NotImplementedError()
                # result = push_service.notify_multiple_devices(
                #     registration_ids=registration_ids,
                #     **kwargs
                # )
                # response.append(result)
        return response

    def send_message(self, title, message, action='just_popup_action', **kwargs):
        # FCM / GCM
        payload = MessageProtocol(title, message, action, **kwargs)
        responses = {}
        if self.fcm_devices:
            responses['fcm'] = self.fcm_send_message(self.fcm_devices, payload.message, **payload.as_dict())

        # APNS
        if self.apn_devices:
            responses['apn'] = self.apn_send_message(self.fcm_devices, payload.message, **payload.as_dict())
        pprint(responses)
        return responses


class LogisticsPushNotification(PushNotification):
    
    USER_TYPE = (settings.DELIVERY_BOY, )
    
    def __init__(self, trip, order = None):
        self.trip = trip
        self.order = order
        super(LogisticsPushNotification, self).__init__(trip.agent)

    def send_cancellation_message(self, order: Order):
        title = f"Cancelled {len(order)} Item(s) from #{order.number}"
        message = ", ".join([i.product_title for i in order.lines.all()])
        self.send_message(title, message)

    def send_trip_started_message(self):
        title = f"Grocery Logistics"
        message = "New Trip has been assigned to you!"
        self.send_message(title, message)

    def send_trip_completed_message(self):
        title = f"Grocery Logistics"
        message = "You have successfully completed the trip."
        self.send_message(title, message)


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


class OrderStatusPushNotification(PushNotification):
    USER_TYPE = (settings.CUSTOMER, )

    def send_status_update(self, order, new_status):
        title = OSCAR_ORDER_STATUS_CHANGE_MESSAGE[new_status]['title'].format(order=order)[:256]
        message = OSCAR_ORDER_STATUS_CHANGE_MESSAGE[new_status]['message'].format(order=order)[:256]
        kwargs = {
                'order_id': order.id,
                'order_number': order.number,
                'order_status': new_status,
        }
        self.send_message(title, message, action='open_orders', extra_notification_kwargs=kwargs)

    def send_refund_update(self, order, amount):
        title = "Refund Initiated!"
        message = f"Refund of amount of {amount} has been Initiated!"
        kwargs = {
            'order_id': order.id,
            'order_number': order.number,
            'amount': amount,
        }
        self.send_message(title, message, action='open_orders', extra_notification_kwargs=kwargs)


class NewOfferPushNotification(PushNotification):
    USER_TYPE = (settings.CUSTOMER, )

    def __init__(self, *users):         # noqa
        self.fcm_devices: GCMDeviceQuerySet = GCMDevice.objects.filter() or None
        self.apn_devices: APNSDeviceQuerySet = APNSDevice.objects.filter() or None






















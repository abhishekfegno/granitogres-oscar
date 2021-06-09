from pprint import pprint

from django.conf import settings
from push_notifications.models import GCMDevice, APNSDevice, APNSDeviceQuerySet, GCMDeviceQuerySet
from pyfcm import FCMNotification

from apps.logistics.models import DeliveryTrip
from apps.order.models import Order


class MessageProtocol:
    title = None
    message = None
    action = None
    icon = None

    def __init__(self, title, message, action, icon=None):
        self.title = title
        self.message = message
        self.action = action
        self.icon = icon

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
            'click_action': self.action, 'message_icon': self.icon
        }


class PushNotification:
    """
    Instead od django-push-notification, we are using pyfcm to send message to server!
    since we have got some authentication issue with the package!
    """
    def __init__(self, *users):
        self.fcm_devices: GCMDeviceQuerySet = GCMDevice.objects.filter(user__in=users) or None
        self.apn_devices: APNSDeviceQuerySet = APNSDevice.objects.filter(user__in=users) or None

    def fcm_send_message(self, queryset, message, **kwargs):
        response = []
        cloud_type = "FCM"
        data = kwargs.pop("extra", {})

        if message is not None:
            data["message"] = message

        app_ids = queryset.filter(
            active=True
        ).order_by("application_id").values_list("application_id", flat=True).distinct()

        for app_id in app_ids:

            registration_ids = list(queryset.filter(
                active=True, cloud_message_type=cloud_type, application_id=app_id
            ).values_list("registration_id", flat=True))

            if registration_ids:
                push_service = FCMNotification(
                    api_key=settings.PUSH_NOTIFICATIONS_SETTINGS['APPLICATIONS'][app_id]['API_KEY'])
                result = push_service.notify_multiple_devices(
                    registration_ids=registration_ids,
                    **kwargs
                )
                response.append(result)

        return response

    def apn_send_message(self, queryset, message, **kwargs):
        # TRY DOC https://pypi.org/project/pyapns-client/
        data = kwargs.pop("extra", {})
        if message is not None:
            data["message"] = message
        app_ids = queryset.filter(
            active=True
        ).order_by("application_id").values_list("application_id", flat=True).distinct()
        response = []
        cloud_type = "FCM"
        for app_id in app_ids:
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

    def send_message(self, title, message, action='just_popup_action', icon=None):
        # FCM / GCM
        payload = MessageProtocol(title, message, action, icon)
        responses = {}
        if self.fcm_devices:
            responses['fcm'] = self.fcm_send_message(self.fcm_devices, payload.message, **payload.as_dict())

        # APNS
        if self.apn_devices:
            responses['apn'] = self.apn_send_message(self.fcm_devices, payload.message, **payload.as_dict())
        pprint(responses)
        return responses


class LogisticsPushNotification(PushNotification):

    def __init__(self, trip: DeliveryTrip, order: Order):
        self.trip = trip
        self.order = order
        super(LogisticsPushNotification, self).__init__(trip.agent)

    def send_cancellation_message(self, items):
        title = f"Cancelled {len(items)} Items from "
        message = ", ".join([i.product_title for i in items])
        self.send_message(title, message)

    def send_trip_started_message(self):
        title = f"Grocery Logistics"
        message = "New Trip has been assigned to you!"
        self.send_message(title, message)

    def send_trip_completed_message(self):
        title = f"Grocery Logistics"
        message = "You have successfully completed the trip."
        self.send_message(title, message)

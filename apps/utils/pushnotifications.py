from push_notifications.models import GCMDevice, APNSDevice, APNSDeviceQuerySet, GCMDeviceQuerySet

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
        "title", "body", "icon", "sound", "badge", "color", "tag", "click_action",
        "body_loc_key", "body_loc_args", "title_loc_key", "title_loc_args", "android_channel_id"
        """
        return {
            "title": self.title, "body": self.message + "\nTap to View More!",
            'click_action': self.action, 'icon': self.icon
        }


class PushNotification:

    def __init__(self, *users):
        self.fcm_devices: GCMDeviceQuerySet = GCMDevice.objects.filter(user__in=users) or None
        self.apn_devices: APNSDeviceQuerySet = APNSDevice.objects.filter(user__in=users) or None

    def send_message(self, title, message, action='just_popup_action', icon=None):
        # FCM / GCM
        payload = MessageProtocol(title, message, action, icon)
        if self.fcm_devices:
            self.fcm_devices.send_message(payload.message, **payload.as_dict(), to=f'/topic/{action}')

        # APNS
        if self.apn_devices:
            self.apn_devices.send_message(payload.message, **payload.as_dict(), to=f'/topic/{action}')


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

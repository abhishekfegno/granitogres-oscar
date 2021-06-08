from django.core.management import BaseCommand

from apps.users.models import User
from apps.push.pushnotifications import PushNotification


class Command(BaseCommand):

    def handle(self, *args, **options):
        u = User.objects.get(pk=1)
        PushNotification(u).send_message(
            title="Delivery Boy Notification",
            message="This is a brief description",

        )
        return None
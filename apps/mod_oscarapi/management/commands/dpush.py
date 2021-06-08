from urllib.error import HTTPError

from django.core.management import BaseCommand

from apps.users.models import User
from apps.utils.push.pushnotifications import PushNotification


class Command(BaseCommand):

    def handle(self, *args, **options):
        u = User.objects.get(pk=1)
        title = 'Grocery App Push Notification Testing!'
        message = 'Some Long Message'
        from apps.utils.push.pushnotifications import PushNotification
        try:
            PushNotification(u).send_message(title, message)
        except HTTPError as err:
            print(err)
            print(err.msg)
            print(err.fp)
            print(err.filename)
            print()
        return




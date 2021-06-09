from urllib.error import HTTPError

from django.core.management import BaseCommand

from apps.users.models import User


class Command(BaseCommand):

    def handle(self, *args, **options):
        u = User.objects.all()
        title = 'Grocery App Push Notification Testing!'
        message = 'Some Long Message'
        from apps.utils.pushnotifications import PushNotification
        try:
            resp = PushNotification(*u).send_message(title, message)
            print("==="*20)
            print(resp)
        except HTTPError as err:
            print(err)
            print(err.msg)
            print(err.fp)
            print(err.filename)
            print()
        return




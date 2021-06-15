import requests
from django.core.management import BaseCommand
from django.urls import reverse


class Command(BaseCommand):
    BASE_URL = 'https://grocery.dev.fegno.com'

    def handle(self, *args, **options):
        url = self.BASE_URL + reverse('api-index-v2')
        print("REQUESTING....", url)
        response = requests.get(url).json()
        for cat in response['']:

        return




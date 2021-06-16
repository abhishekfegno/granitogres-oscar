import requests
from django.core.management import BaseCommand
from django.urls import reverse


class Command(BaseCommand):
    BASE_URL = 'https://grocery.dev.fegno.com'
    # BASE_URL = 'http://localhost:8000'

    def handle(self, *args, **options):
        url = self.BASE_URL + reverse('api-index-v2')
        print("REQUESTING....", url)
        response = requests.get(url).json()
        for cat in response['content']:
            print(cat['name'])
            for prod in cat['products']:
                print('\t', prod['id'], prod['title'], f"\t(Stock:{prod['price']['effective_price']} | QTY: {prod['price']['net_stock_level']})")
                for var in prod['variants']:
                    print('\t\t', var['id'], var['title'],
                          f"\t(Stock:{var['price']['effective_price']} | QTY: {var['price']['net_stock_level']})")
        return




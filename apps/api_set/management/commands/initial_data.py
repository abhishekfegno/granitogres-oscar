from django.core.management import BaseCommand
from oscar.core.loading import get_model

Country = get_model('address', 'Country')


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        india = Country.objects.get_or_create(
            iso_3166_1_a2='IN',
            defaults={
                'iso_3166_1_a3': 'IND',
                'iso_3166_1_numeric': '356',
                'printable_name': 'India',
                'name': 'India',
                'display_order': 0,
                'is_shipping_country': True
            })
        print(Country.objects.all().update(is_shipping_country=True))
        print(Country.objects.all())







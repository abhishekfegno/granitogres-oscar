from django.core.cache import cache
from django.core.management import BaseCommand

from apps.catalogue.models import Product
from lib import cache_key


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        hashmap = []

        for p in Product.objects.all().order_by('-id'):
            if p.title.lower() in hashmap:
                print(f"FOUND '{p.title.lower()}' AS DUPLICATE")
                p.delete()
            else:
                hashmap.append(p.title.lower())
                print(f"FOUND '{p.title.lower()}' AS NEW")




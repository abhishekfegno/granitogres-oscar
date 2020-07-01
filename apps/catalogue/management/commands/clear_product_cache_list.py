from django.core.cache import cache
from django.core.management import BaseCommand

from apps.catalogue.models import Product
from lib import cache_key


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        for p in Product.objects.all():
            # p.save()
            p.clear_list_caches()


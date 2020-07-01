from django.contrib.postgres.search import SearchVector
from django.core.management import BaseCommand

from apps.catalogue.models import Product
from lib import cache_key


class Command(BaseCommand):
    """
    python manage.py recalculate_price_cache
    """
    def handle(self, *args, **kwargs):
        for p in Product.objects.all():
            p._save_price()
            p.save()
            p.clear_price_caches()
            Product.objects.all().update(
                search=SearchVector('title', weight='A') # + SearchVector('description', weight='D'))
            )











from django.core.management import BaseCommand

from apps.catalogue.models import Product


class Command(BaseCommand):

    def handle(self, *args, **options):
        update_list = []
        for p in Product.objects.all().prefetch_related('attributes', 'categories').select_related('brand', 'product_class'):
            p.generate_search()
            update_list.append(p)
        Product.objects.bulk_update(update_list, ['search_tags'])





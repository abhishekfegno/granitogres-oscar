from django.core.management import BaseCommand

from apps.catalogue.models import Product


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        hashmap = []
        products_to_be_deleted = []
        count = Product.objects.all().count()
        print(f"Processing {count} products")
        for p in Product.objects.all().order_by('-id'):
            if p.title.lower() in hashmap:
                products_to_be_deleted.append(p.pk)
                print(f"FOUND '{p.title.lower()}' AS DUPLICATE")
            else:
                hashmap.append(p.title.lower())
                print(f"FOUND '{p.title.lower()}' AS NEW")
        print(f"Found {len(hashmap)} as new products")
        print(f"Found {len(products_to_be_deleted)} items remaining as duplicates of above to be deleted")

        conformation = input(f"Do want to clear these {len(products_to_be_deleted)} items?").lower() in ['Y', 'Yes']
        if conformation:
            Product.objects.filter(id__in=products_to_be_deleted)



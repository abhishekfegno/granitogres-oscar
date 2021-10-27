from django.core.management import BaseCommand

from apps.catalogue.models import ProductAttribute


class Command(BaseCommand):

    def handle(self, *args, **options):
        fields = 'id', 'product_class__name', 'name', 'is_varying'
        qs = ProductAttribute.objects.all().values_list(*fields).order_by('id')
        lines = ["\t ".join([str(j) for j in i]) for i in qs]
        for line in lines:
            print(line)

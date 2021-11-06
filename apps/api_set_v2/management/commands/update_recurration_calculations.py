from django.core.management import BaseCommand
from django.db.models import Count

from apps.catalogue.models import ProductAttributeValue, ProductAttribute
from django.db.models.functions import Upper


class Command(BaseCommand):

    def handle(self, *args, **options):
        ProductAttributeValue.objects.filter(
            attribute__type=ProductAttribute.TEXT
        ).update(value_text=Upper('value_text'))
        # ProductAttributeValue.objects.filter(
        #     attribute__type=ProductAttribute.TEXT
        # ).order_by('value_text').distinct('value_text').values_list(
        #     'id', 'attribute__name', 'value_text', 'product_count'
        # )
        for pc in ProductAttributeValue.objects.filter(attribute__type=ProductAttribute.TEXT).annotate(
                count=Count('pk')).values('value_text', 'count'):
            ProductAttributeValue.objects.filter(attribute__type=ProductAttribute.TEXT,
                                                 value_text=pc['value_text']).update(product_count=pc['count'])
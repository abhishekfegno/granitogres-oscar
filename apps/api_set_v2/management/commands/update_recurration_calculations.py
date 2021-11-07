from django.core.management import BaseCommand
from django.db.models import Count
from oscar.apps.catalogue.models import ProductClass

from apps.catalogue.models import ProductAttributeValue, ProductAttribute
from django.db.models.functions import Upper


class Command(BaseCommand):

    def handle(self, *args, **options):

        ProductAttributeValue.objects.filter(
            attribute__type=ProductAttribute.TEXT,
        ).update(value_text=Upper('value_text'))
        # ProductAttributeValue.objects.filter(
        #     attribute__type=ProductAttribute.TEXT
        # ).order_by('value_text').distinct('value_text').values_list(
        #     'id', 'attribute__name', 'value_text', 'product_count'
        # )

for pc in ProductClass.objects.all():
    _inner_out = {}
    for pa in ProductAttributeValue.objects.filter(attribute__type=ProductAttribute.TEXT, attribute__product_class=pc).values('value_text', 'product_count'):
        if pa['value_text'] not in _inner_out:
            _inner_out[pa['value_text']] = 0
        _inner_out[pa['value_text']] += pa['product_count']

    for val, cnt in _inner_out.items():
        ProductAttributeValue.objects.filter(attribute__type=ProductAttribute.TEXT, attribute__product_class=pc,
                                             value_text=val).update(product_count=cnt)

from django.core.management import BaseCommand
from apps.catalogue.models import Product, ProductAttribute


class Command(BaseCommand):

    def handle(self, *args, **options):

        for p in Product.objects.filter(structure="parent").prefetch_related('children', 'product_class'):
            pc = p.get_product_class()
            for c in p.children.all():
                for attr in pc.attributes.all().values_list('code', flat=True):
                    if attr.endswith('_old') or attr == 'is_present': continue
                    if hasattr(p.attr, attr) and getattr(p.attr, attr):
                        if not hasattr(p.attr, attr):
                            ProductAttribute.objects.create(code=attr, name=attr, product_class=p.get_product_class())
                        if hasattr(p.attr, attr) or not getattr(c.attr, attr):
                            val = getattr(p.attr, attr)
                            setattr(c.attr, attr, val)
                print(c, " Saving ... ")
                c.attr.save()




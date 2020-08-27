from django.core.management import BaseCommand
from faker import Faker

from apps.catalogue.models import Product, Category


class Command(BaseCommand):

    def handle(self, *args, **options):
        p_list = Product.objects.all()
        c_list = Category.objects.all()

        p_fields = ['about', 'storage_and_uses', 'benifits', 'other_product_info', 'variable_weight_policy', 'description']
        c_fields = ['description', ]
        f = Faker()

        for p in p_list:
            for field in p_fields:
                if not getattr(p, field):
                    setattr(p, field, f.paragraph(8))
            print("Updating ", p)
            p.save()

        for c in c_list:
            for field in c_fields:
                if not getattr(c, field):
                    setattr(c, field, f.paragraph(8))
            print("Updating ", c)
            c.save()




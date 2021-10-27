from django.core.management import BaseCommand

from apps.catalogue.models import Product, Category, ProductRecommendation


class Command(BaseCommand):
    qs = Product.objects.filter(structure__in=[Product.STANDALONE, Product.CHILD], is_public=True)

    def get_upselling(self, product, limit=6):
        return self.qs.filter(categories__in=product.categories.all()).exclude(pk=product.pk)[:limit]

    def get_crossselling(self, product, limit=6):
        cat = product.categories.all().first()
        if cat is None or not cat.get_ancestors():
            return
        ncat = cat.get_ancestors()
        return self.qs.filter(categories__in=ncat).exclude(pk=product.pk, categories=cat)[:limit]

    def get_recommendation(self, product, limit=6):
        cat = product.categories.all().first()
        if cat is None or not cat.get_ancestors().last():
            return
        ncat = cat.get_ancestors()[0]
        return self.qs.filter(categories__path__startswith=ncat.path).exclude(pk=product.pk, categories=cat)[:limit]

    def handle(self, *args, **options):

        pr = []
        Product.upselling.through.objects.all().delete()
        Product.crossselling.through.objects.all().delete()
        ProductRecommendation.objects.all().delete()
        for product in Product.objects.all():
            qs = self.get_upselling(product) or []
            for recommended in qs:
                product.upselling.add(recommended)
                
            qs = self.get_crossselling(product) or []
            for recommended in qs:
                product.crossselling.add(recommended)
            qs = self.get_recommendation(product) or []
            for recommended in qs:
                pr.append(ProductRecommendation(primary=product, recommendation=recommended))
            print("Populating Products")
        ProductRecommendation.objects.bulk_create(pr, ignore_conflicts=True)


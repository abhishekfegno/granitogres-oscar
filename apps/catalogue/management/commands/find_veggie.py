from django.core.management.base import BaseCommand

from apps.catalogue.models import Category, Product


class Command(BaseCommand):
    help = "Seperate vegetarian and meet products"

    # def add_arguments(self, parser):
    #     parser.add_argument('sample', nargs='+')

    def handle(self, *args, **options):
        vag_cat = Category.objects.filter()
        Product.objects.all()

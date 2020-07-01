from django.core.management.base import BaseCommand
from oscar.core.loading import get_model

Basket = get_model('basket', 'Basket')


class Command(BaseCommand):
    help = """
    --clear-unused
    """

    def add_arguments(self, parser):
        parser.add_argument('--clear-unused', action='store_true', help='Clear all unused Baskets.')

    def handle(self, *args, **options):
        if '--clear_unused' in options:
            Basket.buy_now.old_baskets.delete()


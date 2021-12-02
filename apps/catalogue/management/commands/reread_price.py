from django.core.management import BaseCommand
from apps.catalogue.management.handlers.stockhandler import Handler
from apps.dashboard.custom.models import SiteConfig


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--update-sheet', action='store_true', help='Sync Products and Stock Record.')
        parser.add_argument('--allow-all', action='store_true', help='Sync Products and Stock Record.')

    def handle(self, *args, **options):
        handler = Handler()
        handler.handle(options['update_sheet'], options['allow_all'])


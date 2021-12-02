from django.core.management import BaseCommand
from apps.catalogue.management.handlers.stockhandler import Handler


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--update-sheet', action='store_true', help='Sync Products and Stock Record.')

    def handle(self, *args, **options):
        handler = Handler()
        if options['update_sheet']:
            handler.sync_db_to_sheet()
        else:
            handler.read_from_sheet()


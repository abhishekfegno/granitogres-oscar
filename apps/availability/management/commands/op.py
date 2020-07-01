from django.core.management import BaseCommand


class Command(BaseCommand):

    def handle(self, *args, **options):
        from ...migration_operations import populate_pincode
        from django.apps import apps

        populate_pincode(apps, None)


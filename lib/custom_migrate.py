from django.db.migrations.operations.base import Operation
from django.db.utils import ProgrammingError


class IndexAfterSearchMigration(Operation):
    # If this migration can be run in reverse.
    # Some operations are impossible to reverse, like deleting data.
    reversible = True
    # Can this migration be represented as SQL? (things like RunPython cannot)
    reduces_to_sql = False
    # Should this operation be forced as atomic even on backends with no
    # DDL transaction support (i.e., does it have no DDL, like RunPython)
    atomic = False
    # Should this operation be considered safe to elide and optimize across?
    elidable = False

    def state_forwards(self, app_label, state):
        pass

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        from oscar.core.loading import get_model
        from django.contrib.postgres.search import SearchVector
        product = get_model('catalogue', 'Product')
        product.objects.all().update(search=SearchVector('title', weight='A') + SearchVector('description', weight='D'))

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        pass


class PopulatePriceAfterMigration(Operation):
    # If this migration can be run in reverse.
    # Some operations are impossible to reverse, like deleting data.
    reversible = True
    # Can this migration be represented as SQL? (things like RunPython cannot)
    reduces_to_sql = False
    # Should this operation be forced as atomic even on backends with no
    # DDL transaction support (i.e., does it have no DDL, like RunPython)
    atomic = False
    # Should this operation be considered safe to elide and optimize across?
    elidable = False

    def state_forwards(self, app_label, state):
        pass

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        from oscar.core.loading import get_model
        try:
            from django.contrib.postgres.search import SearchVector
            product = get_model('catalogue', 'Product')
            for pdt in product.objects.all():
                pdt._save_price()
                pdt.save()
                pdt.clear_price_caches()
        except Exception as e:
            print("WARNING : ", e)

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        pass













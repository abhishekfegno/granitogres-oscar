from django.db.models import Exists
from oscar.apps.catalogue.managers import ProductManager


class BrowsableProductManager(ProductManager):

    def browsable(self):
        """
            Excludes non-canonical products and non-public products
        """
        return self.annotate(
            # has_stock=Exists('stockrecord')   # raising issue
        ).filter(
            structure__in=['standalone', 'parent'], is_public=True,     # has_stock=True
        )

    def get_queryset(self):
        return super().get_queryset()














from django.db.models import Exists, Count
from oscar.apps.catalogue.managers import ProductManager


class BrowsableProductManager(ProductManager):

    def browsable(self):
        """
            Excludes non-canonical products and non-public products
        """
        return self.annotate(
            # has_stock=Count('stockrecords')   # raising issue
        ).filter(
            structure__in=['standalone', 'parent'], is_public=True,     # has_stock__gt=0
        )

    def get_queryset(self):
        return super().get_queryset()














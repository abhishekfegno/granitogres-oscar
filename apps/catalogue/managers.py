from oscar.apps.catalogue.managers import ProductManager


class BrowsableProductManager(ProductManager):

    def browsable(self):
        """
        Excludes non-canonical products and non-public products
        """
        return self.filter(structure__in=['standalone', 'child'], is_public=True, stockrecords__isnull=False)

    def get_queryset(self):
        return super().get_queryset()

    def search(self, q):
        return self.get_queryset()













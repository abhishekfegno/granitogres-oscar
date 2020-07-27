from django.db.models import Exists, Count, OuterRef, F
from oscar.apps.catalogue.managers import ProductManager
from oscar.core.loading import get_model


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

    def base_queryset(self):
        """
        Applies select_related and prefetch_related for commonly related
        models to save on queries
        """
        Option = get_model('catalogue', 'Option')
        product_class_options = Option.objects.filter(productclass=OuterRef('product_class'))
        product_options = Option.objects.filter(product=OuterRef('pk'))
        return self.select_related('product_class')\
            .prefetch_related('children', 'product_options', 'product_class__options', 'stockrecords', 'attribute_values'
                              'stockrecords__partner', 'images') \
            .annotate(has_product_class_options=Exists(product_class_options),
                      has_product_options=Exists(product_options), )














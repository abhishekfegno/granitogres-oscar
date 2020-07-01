import oscar.apps.dashboard.catalogue.apps as apps
from oscar.core.loading import get_class


class CatalogueDashboardConfig(apps.CatalogueDashboardConfig):
    name = 'apps.dashboard.catalogue'

    def ready(self):
        super().ready()
        from apps.dashboard.catalogue.views import ProductCreateUpdateView
        self.product_createupdate_view = ProductCreateUpdateView
        from apps.dashboard.catalogue.views import ProductClassCreateView, ProductClassUpdateView
        self.product_class_create_view = ProductClassCreateView
        self.product_class_update_view = ProductClassUpdateView


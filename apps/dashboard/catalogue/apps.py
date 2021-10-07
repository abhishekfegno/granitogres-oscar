import oscar.apps.dashboard.catalogue.apps as apps
from django.conf.urls import url


class CatalogueDashboardConfig(apps.CatalogueDashboardConfig):
    name = 'apps.dashboard.catalogue'

    def ready(self):
        super().ready()
        from apps.dashboard.catalogue.views import CategoryUpdateView, CategoryCreateView
        from apps.dashboard.catalogue.views import BrandListView, BrandCreateView, BrandUpdateView, BrandDeleteView

        self.category_create_view = CategoryCreateView
        self.category_update_view = CategoryUpdateView

        from apps.dashboard.catalogue.views import ProductCreateUpdateView
        self.product_createupdate_view = ProductCreateUpdateView
        from apps.dashboard.catalogue.views import ProductClassCreateView, ProductClassUpdateView
        self.product_class_create_view = ProductClassCreateView
        self.product_class_update_view = ProductClassUpdateView

        self.brand_list_view = BrandListView
        self.brand_create_view = BrandCreateView
        self.brand_update_view = BrandUpdateView
        self.brand_delete_view = BrandDeleteView

    def get_urls(self):
        processed_urls = super(CatalogueDashboardConfig, self).get_urls()
        urls = [
            url(r'^brands/$', self.brand_list_view.as_view(),
                name='catalogue-brand-list'),
            url(r'^brands/create/$', self.brand_create_view.as_view(),
                name='catalogue-brand-create'),
            url(r'^brands/(?P<pk>\d+)/update/$',
                self.brand_update_view.as_view(),
                name='catalogue-brand-update'),
            url(r'^brands/(?P<pk>\d+)/delete/$',
                self.brand_delete_view.as_view(),
                name='catalogue-brand-delete'),
        ]
        return processed_urls + self.post_process_urls(urls)



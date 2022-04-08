import oscar.apps.dashboard.catalogue.apps as apps
from django.conf.urls import url
from django.urls import path, include


class CatalogueDashboardConfig(apps.CatalogueDashboardConfig):
    name = 'apps.dashboard.catalogue'
    permissions_map = _map = {
        'catalogue-product': (['is_staff'], ['partner.dashboard_access']),
        'catalogue-product-create': (['is_staff'], ['partner.dashboard_access']),
        'catalogue-product-list': (['is_staff'], ['partner.dashboard_access']),
        'catalogue-product-delete': (['is_staff'], ['partner.dashboard_access']),
        'catalogue-product-lookup': (['is_staff'], ['partner.dashboard_access']),
    }

    def ready(self):
        super().ready()
        from apps.dashboard.catalogue.views import (
            CategoryUpdateView, CategoryCreateView,
            BrandListView, BrandCreateView, BrandUpdateView, BrandDeleteView,
            Product360ImageDeleteView, Product360ImageListView,
            Product360ImageCreateView, Product360ImageUpdateView
        )

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

        self.product_360_list_view = Product360ImageListView
        self.product_360_create_view = Product360ImageCreateView
        self.product_360_update_view = Product360ImageUpdateView
        self.product_360_delete_view = Product360ImageDeleteView

    def get_urls(self):
        processed_urls = super(CatalogueDashboardConfig, self).get_urls()
        urls = [
            path('brands/', include([
                url(r'^$', self.brand_list_view.as_view(),
                    name='catalogue-brand-list'),
                url(r'^create/$', self.brand_create_view.as_view(),
                    name='catalogue-brand-create'),
                url(r'^(?P<pk>\d+)/update/$',
                    self.brand_update_view.as_view(),
                    name='catalogue-brand-update'),
                url(r'^(?P<pk>\d+)/delete/$',
                    self.brand_delete_view.as_view(),
                    name='catalogue-brand-delete'),
            ])),
            path('product-360/', include([
                url(r'^$', self.product_360_list_view.as_view(),
                    name='catalogue-product360-list'),
                url(r'^create/$', self.product_360_create_view.as_view(),
                    name='catalogue-product360-create'),
                url(r'^(?P<pk>\d+)/update/$',
                    self.product_360_update_view.as_view(),
                    name='catalogue-product360-update'),
                url(r'^(?P<pk>\d+)/delete/$',
                    self.product_360_delete_view.as_view(),
                    name='catalogue-product360-delete'),
            ]))
        ]
        return processed_urls + self.post_process_urls(urls)



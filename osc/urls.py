"""osc URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import os

import debug_toolbar
from django.apps import apps
from django.conf import settings
from django.conf.urls import url
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.flatpages.models import FlatPage
from django.contrib.flatpages.sitemaps import FlatPageSitemap
from django.contrib.sitemaps.views import sitemap
from django.shortcuts import render
from django.urls import path, include
from django.views.decorators.cache import never_cache
from django.views.generic import TemplateView
from rest_framework.decorators import api_view
from rest_framework.documentation import include_docs_urls
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from apps.dashboard.catalogue.views import ProductRedirectView, CatalogueRedirectView
from apps.mod_oscarapi.views.checkout import CheckoutView
from django.views.i18n import JavaScriptCatalog

view_checkout = never_cache(CheckoutView.as_view())


@api_view()
def policy_html(request, path):
    flatpage = get_object_or_404(FlatPage.objects.filter(), url=path)
    return Response({
        'title': flatpage.title,
        'url': flatpage.url,
        'content': flatpage.content,
        'registration_required': flatpage.registration_required,
    })


urlpatterns = [
    path('api/v1/checkout/', view_checkout, name='api-checkout'),                   # Must be before oscar_api.urls
    path('api/v2/checkout/', view_checkout, name='api-checkout'),                   # Must be before oscar_api.urls
    # path('api/v1/', include(apps.get_app_config("oscarapicheckout").urls[0])),    # Must be before oscar_api.urls

    path('api/v1/', include('oscarapi.urls')),
    path('api/v1/buy-now/', include('apps.buynow.urls')),
    path('api/v2/', include('oscarapi.urls')),
    path('api/v2/buy-now/', include('apps.buynow.urls')),

    path('api/', include('apps.api_set.urls')),                                      # prone to versioning
    path('api/v2/', include('apps.api_set_v2.urls')),                                # prone to versioning

    path('api/v1/', include('apps.logistics.apis')),                                 # prone to versioning
    path('api/v2/', include('apps.logistics.apis')),                                 # prone to versioning

    path('api/v2/avalilability/', include('apps.availability.api')),
    path('api/v1/avalilability/', include('apps.availability.api')),
    path('dashboard/avalilability/', include('apps.availability.urls')),
    path('dashboard/logistics/', include('apps.logistics.urls')),
    path('dashboard/orders/', include('apps.order.timeslot.urls')),
    path('dashboard/ranges/', include('apps.dashboard.ranges.urls')),
    # path('dashboard/communication/', include('apps.dashboard.communications.urls')),
    # https://github.com/django-oscar/django-oscar-accounts
    path('dashboard/accounts/', apps.get_app_config('accounts_dashboard').urls),

    # path('catalogue/<slug:slug>'+'_<int:pk>/', ProductRedirectView.as_view(), name='product-detail-api'),###API of product detail
    # path('catalogue/', CatalogueRedirectView.as_view(), name='catalogue_redirect'),

    # path(r'dashboard/payments/cod/', include(cod_app.urls)),
    path('sitemap.xml', sitemap,
         {'sitemaps': {'flatpages': FlatPageSitemap}},
         name='django.contrib.sitemaps.views.sitemap'),

    path('api/docs/', include_docs_urls(title='Fegno Store API', public=True)),
    path('i18n/', include('django.conf.urls.i18n')),  # > Django-2.0
    path('admin/', admin.site.urls),

    path('api/v2/push/', include('apps.utils.push_urls')),
    path('api/v1/push/', include('apps.utils.push_urls')),
    path('api/v2/policies<path:path>', policy_html, name="policies"),
    path('dashboard/', include('couriers.delhivery.urls')),
    path('', include('apps.users.urls')),
    path('', include('apps.dashboard.custom.urls')),
    path('', include(apps.get_app_config('oscar').urls[0])),  # > Django-2.0

    # url(r'^ckeditor/', include('ckeditor.urls')),
    url(r'^ckeditor/', include('ckeditor_uploader.urls')),

]

# if 'stores' in settings.INSTALLED_APPS:
#     urlpatterns += [
#         # basic configuration for Oscar
#         path('', include(apps.get_app_config('oscar').urls[0])),
#         # adds URLs for the dashboard store manager
#         path('dashboard/stores/', apps.get_app_config('stores_dashboard').urls),
#         # adds URLs for overview and detail pages
#         path('stores/', apps.get_app_config('stores').urls),
#         # adds internationalization URLs
#         path('jsi18n/', JavaScriptCatalog.as_view(), name='javascript-catalog'),
#     ]


if settings.DEBUG:
    urlpatterns.append(path('__debug__/', include(debug_toolbar.urls))),
    urlpatterns += static(settings.STATIC_URL, document_root=os.path.join(settings.BASE_DIR, "assets"))
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += path('qs/', TemplateView.as_view(template_name="dummy_search.html")),  # > Django-2.0
    urlpatterns += path('sentry-debug/', lambda request: 1 / 0),


def error_404(request, exception=None):
    return render(request, '404.html', status=404)


def error_500(request, exception=None):
    return render(request, '500.html', status=500)


def error_400(request, exception=None):
    return render(request, '400.html', status=400)


def error_403(request, exception=None):
    return render(request, '403.html', status=403)


handler500 = error_500
handler403 = error_403
handler400 = error_400
handler404 = error_404


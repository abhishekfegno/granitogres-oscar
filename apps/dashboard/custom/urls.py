import errno
import os

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import path, include, reverse, reverse_lazy
from django.views.generic import TemplateView, UpdateView, FormView

from apps.api_set_v2.views.google_merchant_format import call_merchant
from apps.catalogue.management.handlers.stockhandler import Handler
from apps.dashboard.custom.models import models_list, SiteConfig
from apps.dashboard.custom.views.general import DashboardBlockList, DashboardCustomCreate, DashboardCustomDetail, \
    DashboardCustomDelete, BrochureCreateView, GalleryCreateView, get_album_form, delete_brochure, delete_gallery, \
    BrochureUpdateView, GalleryUpdateView
from apps.dashboard.custom.views.offer_banner import OfferBannerList, OfferBannerDetail, OfferBannerCreate, \
    OfferBannerDelete

app_name = 'dashboard-custom'


class UpdateSiteConfig(UpdateView):
    def get_object(self, queryset=None):
        return SiteConfig.get_solo()
    template_name = "dashboard/site-config.html"
    fields = "__all__"

    def get_success_url(self):
        return reverse('dashboard-custom:site-config')


class Rzp(TemplateView):
    template_name = "oscar/checkout/payment_details_sample.html"

    def get_context_data(self, **kwargs):
        class Ordt:
            incl_tax = self.request.GET.get('amt')

        order_total = Ordt()

        return super(Rzp, self).get_context_data(
            order_total_incl_tax_cents=self.request.GET.get('amt'),
            order_total=order_total, user=self.request.user
        )

    def post(self, request, *args, **kwargs):
        print(self.request.POST['razorpay_payment_id'])
        return HttpResponseRedirect(reverse('dashboard-custom:rzp'))


class UpdateSheetSynchronization(TemplateView):
    template_name = "dashboard/sheet_synchronization.html"
    success_url = reverse_lazy('dashboard-custom:sheet-synchronization')

    def get_context_data(self, **kwargs):
        return super(UpdateSheetSynchronization, self).get_context_data(config=SiteConfig().get_solo(), **kwargs)

    def post(self, request, *args, **kwargs):
        caller_function = request.POST.get('update_sheet', None)
        try:
            handler = Handler()
            getattr(handler, caller_function)()
            # caller_function can be: sync_db_to_sheet, sync_stock_from_sheet_to_db, sync_price_from_db_to_sheet
        except Exception as e:
            messages.error(self.request, "Something went wrong! " + str(e))
        else:
            self.get_proper_message(caller_function)
        return redirect(self.get_success_url())

    def get_proper_message(self, caller_function):
        msg = {
            "sync_sheet_with_db": "Sheet has been Updated Successfully!",
            "sync_stock_from_sheet_to_db": "New Stock counts has been Updated to Database!",
            "sync_price_from_db_to_sheet": "New Price changes has been Updated to Database!",
        }.get(caller_function)
        messages.success(self.request, msg)

    def get_success_url(self):
        return self.success_url


def view_set(slug, l=None, c=None, r=None, d=None):
    c = c or {}
    r = r or {}
    l = l or {}
    d = d or {}
    return include([
        path('', DashboardBlockList.as_view(**l), name=f"dashboard-{slug}-list"),
        path('create/', DashboardCustomCreate.as_view(**c), name=f"dashboard-{slug}-create"),
        path('<int:pk>/', DashboardCustomDetail.as_view(**r), name=f'dashboard-{slug}-detail'),
        path('<int:pk>/delete/', DashboardCustomDelete.as_view(**d), name=f'dashboard-{slug}-delete'),
    ])


referrers = []

for _model in models_list:
    referrers.append(path(f'{_model.referrer}/', view_set(_model.referrer)),)


urlpatterns = [
    path('dashboard/', include([
                                   path('offer-banner/', include([
                                       path('', OfferBannerList.as_view(), name="dashboard-offer-banner-list"),
                                       path('create/', OfferBannerCreate.as_view(), name="dashboard-offer-banner-create"),
                                       path('<int:pk>/', OfferBannerDetail.as_view(), name='dashboard-offer-banner-detail'),
                                       path('<int:pk>/delete/', OfferBannerDelete.as_view(), name='dashboard-offer-banner-delete'),
                                   ])),
                                   path("google_merchant_format/", call_merchant, name="product_list_google_merchant"),
                                   path("brochure", BrochureCreateView.as_view(), name="dashboard-brochure-create"),
                                   path("brochure/delete/<int:id>/", delete_brochure, name="dashboard-brochure-delete"),
                                   path("brochure/edit/<int:pk>/", BrochureUpdateView.as_view(), name="dashboard-brochure-update"),
                                   path("gallery", GalleryCreateView.as_view(), name="dashboard-gallery-create"),
                                   path("gallery/edit/<int:pk>/",  GalleryUpdateView.as_view(), name="dashboard-gallery-update"),
                                   path("gallery/delete/<int:id>/", delete_gallery, name="dashboard-gallery-delete"),
                                   path("get/albumform/", get_album_form, name="get_album_form"),
                                   path('site-configuration', UpdateSiteConfig.as_view(), name="site-config"),
                                   path('sheet-synchronization', UpdateSheetSynchronization.as_view(), name="sheet-synchronization"),
                               ] + referrers)),
    path('rzp/', Rzp.as_view(), name='rzp'),
]



import errno
import os

from django.http import HttpResponseRedirect
from django.urls import path, include, reverse
from django.views.generic import TemplateView

from apps.dashboard.custom.models import models_list
from apps.dashboard.custom.views.general import DashboardBlockList, DashboardCustomCreate, DashboardCustomDetail, \
    DashboardCustomDelete
from apps.dashboard.custom.views.offer_banner import OfferBannerList, OfferBannerDetail, OfferBannerCreate, \
    OfferBannerDelete

app_name = 'dashboard-custom'


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
    ] + referrers)),
    path('rzp/', Rzp.as_view(), name='rzp'),
]



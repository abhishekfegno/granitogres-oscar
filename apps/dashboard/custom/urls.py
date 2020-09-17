import errno
import os

from django.http import HttpResponseRedirect
from django.urls import path, include, reverse
from django.views.generic import TemplateView

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


urlpatterns = [
    path('dashboard/', include([
        path('offer-banner/', include([
            path('', OfferBannerList.as_view(), name="dashboard-offer-banner-list"),
            path('create/', OfferBannerCreate.as_view(), name="dashboard-offer-banner-create"),
            path('<int:pk>/', OfferBannerDetail.as_view(), name='dashboard-offer-banner-detail'),
            path('<int:pk>/delete/', OfferBannerDelete.as_view(), name='dashboard-offer-banner-delete'),
        ])),
    ])),
    path('rzp/', Rzp.as_view(), name='rzp'),
]



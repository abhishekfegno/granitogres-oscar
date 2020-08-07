from django.urls import path, include

from apps.dashboard.custom.views.offer_banner import OfferBannerList, OfferBannerDetail, OfferBannerCreate, \
    OfferBannerDelete
from apps.dashboard.custom.views import delivery_boy

app_name = 'dashboard-custom'

urlpatterns = [
    path('dashboard/', include([
        path('offer-banner/', include([
            path('', OfferBannerList.as_view(), name="dashboard-offer-banner-list"),
            path('create/', OfferBannerCreate.as_view(), name="dashboard-offer-banner-create"),
            path('<int:pk>/', OfferBannerDetail.as_view(), name='dashboard-offer-banner-detail'),
            path('<int:pk>/delete/', OfferBannerDelete.as_view(), name='dashboard-offer-banner-delete'),
        ])),
        path('delivery-boy/', include([
            path('', delivery_boy.DeliveryBoyList.as_view(), name=f"dashboard-delivery-boy-list"),
            path('<int:pk>/', delivery_boy.actions, name=f"dashboard-delivery-boy-update"),
        ]))
    ]))
]




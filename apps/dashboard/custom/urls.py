from django.urls import path, include

from apps.dashboard.custom.views.offer_banner import OfferBannerList, OfferBannerDetail, OfferBannerCreate

urlpatterns = [
    path('dashboard/', include([
        path('offer-banner/', OfferBannerList.as_view(), name="dashboard-offer-banner-list"),
        path('offer-banner/create/', OfferBannerCreate.as_view(), name="dashboard-offer-banner-create"),
        path('offer-banner/<int:pk>/', OfferBannerDetail.as_view(), name='dashboard-offer-banner-detail'),
        path('offer-banner/<int:pk>/delete/', OfferBannerDetail.as_view(), name='dashboard-offer-banner-delete'),
    ]))
]



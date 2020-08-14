from django.urls import path, include

from . import api_views

app_name = 'logistics-api'

urlpatterns = [
    path('order/', include([
        path('<int:pk>/details/', api_views.OrdersDetailView.as_view(), name="order-detail"),
        path('<int:pk>/action/', api_views.OrdersDetailView.as_view(), name="order-action"),
        path('item/<int:pk>/action/', api_views.OrdersDetailView.as_view(), name="order-item-action"),
    ])),

    path('trips/', include([
        path('active/', api_views.ActiveTripView.as_view(), name="active-trip"),
        path('delivered/', api_views.DeliveredTripsListView.as_view(), name="delivered-list"),
        path('delivered/<int:pk>/detail/', api_views.DeliveredTripsDetailView.as_view(), name="detail-trip"),
    ])),
]

from django.urls import path, include

from . import api_views

app_name = 'logistics-api'

urlpatterns = [
    path('orders/', include([
        path('', api_views.OrdersListView.as_view(), name="order-list"),
        path('<int:pk>/action/', api_views.OrdersDetailView.as_view(), name="order-action"),
        path('item/<int:pk>/action/', api_views.OrdersDetailView.as_view(), name="order-item-action"),
    ])),
    path('trips', api_views.TripsListView.as_view(), name="order-list"),
]

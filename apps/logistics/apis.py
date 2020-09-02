from django.urls import path, include

from . import api_views

app_name = 'logistics-api'

urlpatterns = [
    path('trips/', include([
        path('planned/', api_views.PlannedTripView.as_view(), name="planned-trip"),
        path('active/', api_views.ActiveTripView.as_view(), name="active-trip"),
        path('delivered/', api_views.DeliveredTripsListView.as_view(), name="delivered-list"),
        path('cancelled/', api_views.CancelledTripsListView.as_view(), name="cancelled-list"),
        path('<int:pk>/detail/', api_views.TripsDetailView.as_view(), name="detail-trip"),
    ])),

    path('logistics/', include([
        path('order/<int:pk>/details/', api_views.orders_detail, name="order-detail"),
        path('order/<int:pk>/details/more/', api_views.orders_detail, name="order-more"),
        path('return/<int:pk>/details/', api_views.orders_item_detail, name="order-item-detail"),
        
        path('<str:method>/<int:pk>/action/<str:action>/', api_views.order_delivered_status_change, name="order-action"),

    ])),

]

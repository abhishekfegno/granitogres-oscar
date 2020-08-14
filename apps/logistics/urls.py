from django.urls import path, include

from apps.logistics.views.generic import ActiveTripsListView, DeliveredTripsListView, TripCreateView, TripUpdateView, \
    PlannedTripsListView
from apps.logistics.views import delivery_boy

app_name = 'logistics'

urlpatterns = [
    path('delivery-agent/', include([
        path('', delivery_boy.DeliveryBoyList.as_view(), name=f"dashboard-delivery-boy-list"),
        path('<int:pk>/', delivery_boy.actions, name=f"dashboard-delivery-boy-update"),
        path('action/<int:pk>/', delivery_boy.actions, name=f"dashboard-delivery-boy-update"),
    ])),

    path('trips/', include([

        path('new/', TripCreateView.as_view(), name="new-trip"),
        path('<int:pk>/', TripUpdateView.as_view(), name="update-trip"),

        path('planned/', PlannedTripsListView.as_view(), name="planned-trips"),
        path('active/', ActiveTripsListView.as_view(), name="active-trips"),
        path('delivered/', DeliveredTripsListView.as_view(), name="delivered-trips"),

    ]))

]






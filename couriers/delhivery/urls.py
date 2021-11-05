from django.urls import path, include
from couriers.delhivery.views import *

app_name = 'dashboard-pickup'

urlpatterns = [
    path('pickup/', include([
        path('', DashboardPickupListView.as_view(), name='list'),
        path('create/', DashboardPickupCreateView.as_view(), name='create'),
        path('<int:pk>/update>/', DashboardPickupUpdateView.as_view(), name='update'),
        path('<int:pk>/delete/', DashboardPickupDeleteView.as_view(), name='delete'),
    ]))
]

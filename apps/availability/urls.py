from django.urls import path

from apps.availability.pincode.views import PincodeSelector
from apps.availability.zones.views import *

pincode_selector = PincodeSelector.as_view()
zone_list = ZoneSelector.as_view()
zone_create = ZoneCreate.as_view()
zone_update = ZoneUpdate.as_view()
zone_delete = ZoneDelete.as_view()
app_name = 'availability'


urlpatterns = [
    path('pincode/', pincode_selector, name='pincode-selector'),
    path('zones/', zone_list, name='zones-list'),
    path('zones/create/', zone_create, name='zones-create'),
    path('zones/<int:pk>/update/', zone_update, name='zones-update'),
    path('zones/<int:pk>/delete/', zone_delete, name='zones-delete'),
]


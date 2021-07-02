from django.urls import path, include

from apps.order.timeslot.views import *

urlpatterns = [
    path('timeslots/', include([
        path('', TimeSlotConfigurationListView.as_view(), name="timeslotconfiguration-list"),
        path('generated', TimeSlotListView.as_view(), name="timeslot-list"),
        path('create/', TimeSlotConfigurationCreateView.as_view(), name="timeslotconfiguration-create"),
        path('<int:pk>/', TimeSlotConfigurationUpdateView.as_view(), name="timeslotconfiguration-update"),
    ]))
]

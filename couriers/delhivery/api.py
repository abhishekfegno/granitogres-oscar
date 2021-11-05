from django.urls import path
from rest_framework.decorators import api_view
from rest_framework.response import Response

from couriers.delhivery.facade import Delhivery


@api_view()
def track_waybill(request, waybill):
    d = Delhivery()
    out, status = d.track_order(waybill=waybill)
    return Response(out, status=status)


urlpatterns = [
    path('track/<str:waybill>/', track_waybill, name="track-waybill"),
]


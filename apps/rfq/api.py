from django.urls import path

from apps.rfq.views import RFQCreateAPIView

urlpatterns = [
    path('rfq', RFQCreateAPIView.as_view(), name="rfq")
]

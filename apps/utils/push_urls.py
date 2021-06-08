from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.utils.rest_framework import APNSDeviceAuthorizedViewSet, GCMDeviceAuthorizedViewSet

router = DefaultRouter()
router.register(r'device/apns', APNSDeviceAuthorizedViewSet)
router.register(r'device/gcm', GCMDeviceAuthorizedViewSet)

urlpatterns = [
    path('', include(router.urls)),
]


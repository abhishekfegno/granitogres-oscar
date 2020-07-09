from django.urls import include, path
from push_notifications.api.rest_framework import APNSDeviceAuthorizedViewSet, GCMDeviceAuthorizedViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'device/apns', APNSDeviceAuthorizedViewSet)
router.register(r'device/gcm', GCMDeviceAuthorizedViewSet)

urlpatterns = [
    # '',             # URLs will show scripted at <api_root>/device/apns
    path('', include(router.urls)),
]

# 861815040245317

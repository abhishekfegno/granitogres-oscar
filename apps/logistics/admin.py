from django.contrib import admin

# Register your models here.
from apps.logistics.models import DeliveryTrip

admin.site.register(DeliveryTrip)

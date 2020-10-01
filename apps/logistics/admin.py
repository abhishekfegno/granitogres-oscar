from django.contrib import admin

# Register your models here.
from apps.logistics.models import DeliveryTrip, ConsignmentDelivery, ConsignmentReturn

admin.site.register(DeliveryTrip)
admin.site.register(ConsignmentDelivery)
admin.site.register(ConsignmentReturn)

from django.contrib import admin

# Register your models here.
from apps.logistics.models import DeliveryTrip, ConsignmentDelivery, ConsignmentReturn, FailedRefund

admin.site.register(DeliveryTrip)
admin.site.register(ConsignmentDelivery)
admin.site.register(ConsignmentReturn)
admin.site.register(FailedRefund)

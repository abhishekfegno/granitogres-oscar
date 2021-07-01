from oscar.apps.order.admin import *  # noqa

from apps.order.models import TimeSlot, TimeSlotConfiguration


class TimeSlotConfigurationAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'index')


admin.site.register(TimeSlotConfiguration, TimeSlotConfigurationAdmin)
admin.site.register(TimeSlot)

from django.contrib import admin
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory
from apps.availability.models import PinCode, Zones


class MyPinCodeAdmin(TreeAdmin):
    form = movenodeform_factory(PinCode)


admin.site.register(PinCode, MyPinCodeAdmin)
admin.site.register(Zones)





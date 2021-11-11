import floppyforms
from django import forms
from django.conf import settings

from apps.availability.models import Zones, PinCode


# class PolyWidget(floppyforms.gis.PolygonWidget, floppyforms.gis.BaseGMapWidget):
#     google_maps_api_key = settings.GOOGLE_MAPS_API_KEY

# class PolyWidget(floppyforms.gis.PolygonWidget, floppyforms.gis.BaseMetacartaWidget):
#     map_width = 600
#     map_height = 400
#
class PolyWidget(floppyforms.gis.PolygonWidget, floppyforms.gis.BaseOsmWidget):
    map_width = 600
    map_height = 400


class ZoneForm(forms.ModelForm):

    name = forms.CharField()
    zone = floppyforms.gis.PolygonField(
        widget=PolyWidget,
        required=False)
    pincode = forms.ModelMultipleChoiceField(
        queryset=PinCode.objects.filter(code__isnull=False),
        required=False)

    class Meta:
        model = Zones
        fields = ('name', 'zone', 'partner', 'pincode')


class ZoneGeolocationForm(ZoneForm):
    pincode = None

    class Meta:
        model = Zones
        fields = ('name', 'zone', 'partner', 'is_default_zone', )


class ZonePincodeForm(ZoneForm):
    zone = None

    class Meta:
        model = Zones
        fields = ('name', 'pincode', 'partner', 'is_default_zone', )


class ZoneFormSelector(object):

    def select_form_class(self):
        if settings.LOCATION_FETCHING_MODE == settings.PINCODE:
            return ZonePincodeForm
        if settings.LOCATION_FETCHING_MODE == settings.GEOLOCATION:
            return ZoneGeolocationForm
        return ZoneForm







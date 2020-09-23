import floppyforms
from django import forms
from django.conf import settings

from apps.availability.models import Zones


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

    zone = floppyforms.gis.PolygonField(widget=PolyWidget)
    name = forms.CharField()

    class Meta:
        model = Zones
        fields = ('name', 'zone', 'partner', )









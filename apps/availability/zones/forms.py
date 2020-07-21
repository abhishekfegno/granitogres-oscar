import floppyforms
from django import forms
from django.conf import settings

from apps.availability.models import Zones


# class PolyWidget(floppyforms.gis.PolygonWidget, floppyforms.gis.BaseGMapWidget):
#     google_maps_api_key = settings.GOOGLE_MAPS_API_KEY

class PolyWidget(floppyforms.gis.PolygonWidget, floppyforms.gis.BaseOsmWidget):
    pass


class ZoneForm(forms.ModelForm):

    zone = floppyforms.gis.PolygonField(widget=PolyWidget(attrs={
        'map_width': 1000,
        'map_height': 700,
    }))
    name = forms.CharField(widget=forms.TextInput(attrs={'class': "form-control"}))

    class Meta:
        model = Zones
        fields = ('name', 'zone', 'partner', )









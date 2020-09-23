from django import forms
from django.contrib.gis.gdal import GDALException
from django.contrib.gis.geos import Point
from rest_framework import serializers

from apps.availability.zones.facade import ZoneFacade
from apps.users.models import Location


class PointSerializer(serializers.Serializer):
    longitude = serializers.DecimalField(max_digits=24, decimal_places=16,)
    latitude = serializers.DecimalField(max_digits=24, decimal_places=16,)

    def validate(self, attrs):
        try:
            x, y = float(attrs['longitude']), float(attrs['latitude'])
            attrs['point'] = Point(x, y)
        except GDALException as e:
            raise forms.ValidationError(e)
        return attrs


class DeliverabilityCheckSerializer(PointSerializer):

    def validate(self, attrs):
        attrs = super(DeliverabilityCheckSerializer, self).validate(attrs)
        zone = ZoneFacade().check_deliverability(point=attrs['point'])
        if not zone:
            raise forms.ValidationError("Currently we are not delivering to this location.")
        location_id = self.context['request'].session.get('location_id')
        if location_id:
            location = Location.objects.filter(id=location_id, is_active=True).last()
            if location and location.location == attrs['point']:
                forms.ValidationError("Location Already Updated!")
        attrs['zone'] = zone
        return attrs






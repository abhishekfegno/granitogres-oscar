from django import forms
from django.conf import settings
from django.contrib.gis.gdal import GDALException
from django.contrib.gis.geos import Point
from rest_framework import serializers

from apps.availability.facade import ZoneFacade
from apps.users.models import Location


class PointSerializer(serializers.Serializer):

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass

    longitude = serializers.DecimalField(
        max_digits=24, decimal_places=16,
        allow_null=settings.LOCATION_FETCHING_MODE != settings.GEOLOCATION,
    )
    latitude = serializers.DecimalField(
        max_digits=24, decimal_places=16,
        allow_null=settings.LOCATION_FETCHING_MODE != settings.GEOLOCATION,
    )

    def validate(self, attrs):
        try:
            if attrs.get('longitude') and attrs.get('latitude'):
                x, y = float(attrs['longitude']), float(attrs['latitude'])
                attrs['point'] = Point(x, y)
        except GDALException as e:
            raise forms.ValidationError(e)
        return attrs


class ZonalDataSerializer(PointSerializer):
    pincode = serializers.CharField(
        max_length=8, min_length=6,
        required=settings.LOCATION_FETCHING_MODE == settings.PINCODE,
        allow_null=settings.LOCATION_FETCHING_MODE != settings.PINCODE,
    )
    longitude = serializers.DecimalField(
        max_digits=24, decimal_places=16,
        allow_null=settings.LOCATION_FETCHING_MODE != settings.GEOLOCATION,
        required=settings.LOCATION_FETCHING_MODE == settings.GEOLOCATION)
    latitude = serializers.DecimalField(
        max_digits=24, decimal_places=16,
        allow_null=settings.LOCATION_FETCHING_MODE != settings.GEOLOCATION,
        required=settings.LOCATION_FETCHING_MODE == settings.GEOLOCATION)


class DeliverabilityCheckSerializer(ZonalDataSerializer):

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        # import pdb;pdb.set_trace()
        if settings.LOCATION_FETCHING_MODE == settings.GEOLOCATION:
            key = 'point'
        elif settings.LOCATION_FETCHING_MODE == settings.PINCODE:
            key = 'pincode'
        validated_data['facade_object'].set_zone(self.context['request'])

    def validate(self, attrs):
        key = ''
        if settings.LOCATION_FETCHING_MODE == settings.GEOLOCATION:
            attrs = super().validate(attrs)
            key = 'point'
        elif settings.LOCATION_FETCHING_MODE == settings.PINCODE:
            key = 'pincode'
        facade_object = ZoneFacade(attrs[key])
        if not facade_object.is_valid():
            raise forms.ValidationError("Sorry, We are unable to deliver to this location now!")
        zone = facade_object.get_zone()
        # location_id = self.context['request'].session.get('location')
        # if location_id:
        #     location = Location.objects.filter(id=location_id, is_active=True).last()
        #     if location and location.location == attrs[key]:
        #         forms.ValidationError("Location Already Updated!")
        attrs['zone'] = zone
        attrs['facade_object'] = facade_object
        return attrs




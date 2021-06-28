from typing import Optional

from django.conf import settings
from django.contrib.gis.db.models import PointField

from apps.availability.models import Zones, PinCode
from apps.users.models import Location


class BaseZoneFacade(object):

    def __init__(self, info_object):
        """
        this info object will be an "Point" object for Geolocation, "Pincode" for Pincode based Locations and so on!
        """
        self.info_object = info_object

    __zone = None

    def check_deliverability(self) -> bool:
        raise NotImplementedError()

    def save(self) -> None:
        raise NotImplementedError()

    def get_zone(self) -> Zones:
        raise NotImplementedError()

    def get_params_for_location(self) -> dict:
        return {}

    def set_zone(
            self, request,
            zone: Zones = None,
    ):
        if request.user.is_authenticated:
            user = request.user
            Location.objects.filter(user=user).update(is_active=False)
        else:
            user = None
        params = self.get_params_for_location()
        if 'user' in params:
            del params['user']
        if 'is_active' in params:
            del params['is_active']
        location = Location.objects.create(**params, user=user, is_active=True if user else False)
        self.set_session(request, zone, location)
        return self.face(request)

    def face(self, request, zone=None, location=None):
        if location is None:
            location = Location.objects.filter(pk=request.session.get('location')).order_by('id').last().select_related('zone')
        if zone is None and location is not None:
            zone = location.zone

        out = {
            "zone_id": location.zone_id,
            "zone_name": location.zone.name,
            "location_id": location.id,
            "location_name": location.name,
            'location_coordinates': str(location.location),
        }
        for MODE in settings.LOCATION_FETCHING_MODE_SET:
            attr_name = f'get_{MODE}_data'
            if attr_name in
            out[MODE] =
        return out

    def _get_zone(self):
        pass

    def set_session(self, request, zone: Zones, location: Location) -> None:
        request.session['location'] = location.pk
        request.session['location_name'] = location.location_name or settings.DEFAULT_LOCATION_NAME
        request.session['zone'] = zone.pk
        request.session['zone_name'] = zone.name
        request.session['pincode'] = location.pincode

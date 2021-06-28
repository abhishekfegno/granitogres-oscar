from typing import Optional

from django.conf import settings
from django.contrib.gis.db.models import PointField

from apps.availability.models import Zones, PinCode
from apps.users.models import Location


class ZoneFacade(object):

    def check_deliverability(self, point=None, pincode=None):
        return Zones.objects.filter(zone__bbcontains=point).order_by('-id').first()

    def _set_geolocation_based_zone(self, zone, **kwargs):
        return {
            "location": kwargs['point'],
            "location_name": kwargs.get('location_name', settings.DEFAULT_LOCATION_NAME),
            "zone": zone
        }

    def _set_pincode_based_zone(self, zone, **kwargs):
        return {
            "pincode": kwargs['pincode'].code,
            "location_name": kwargs.get(kwargs['pincode'].name, settings.DEFAULT_LOCATION_NAME),
            "zone": zone
        }

    def get_params_method(self):
        attr_name = f'set_{settings.LOCATION_FETCHING_MODE}_based_zone'
        if hasattr(self, attr_name) and callable(getattr(self, attr_name)):
            return getattr(self, attr_name)
        raise NotImplementedError(f'You need to implement a callable method "def {attr_name}(self, **kwargs)" to the '
                                  f'class <apps.availability.zones.ZoneFacade>  since settings.LOCATION_FETCHING_MODE '
                                  f'is defined as "{settings.LOCATION_FETCHING_MODE}"')

    def set_zone(self, request,
                 zone: Zones = None,
                 point: Optional[PointField] = None,
                 pincode: Optional[PinCode] = None):
        if zone:
            user = request.user if request.user.is_authenticated else None
            location_mgr = Location.objects
            if user:
                location_mgr.filter(user=user).update(is_active=False)

            get_params = self.get_params_method()
            params = get_params(zone=zone, point=point, pincode=pincode)
            location = location_mgr.create(**params, user=user, is_active=True if user else False)
            request.session['location'] = location.id
            request.session['location_name'] = location.location_name or settings.DEFAULT_LOCATION_NAME
            request.session['zone'] = zone.id
            request.session['zone_name'] = zone.name
            request.session['pincode'] = location.pincode
        return self.face(request)

    def face(self, request):
        return {
            "zone_id": request.session.get('zone'),
            "zone_name": request.session.get('zone_name'),
            "location_id": request.session.get('location'),
            "location_name": request.session.get('location_name'),
            'location_coordinates': request.session.get('location_coordinates'),
            'pincode': request.session.get('pincode'),
        }

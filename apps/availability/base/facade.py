from typing import Optional

from django.conf import settings
from django.contrib.gis.db.models import PointField

from apps.availability.models import Zones, PinCode
from apps.users.models import Location


class BaseZoneFacade(object):

    def __init__(self, info_object=None):
        """
        this info object will be an "Point" object for Geolocation, "Pincode" for Pincode based Locations and so on!
        """
        self.info_object = info_object

    __zone = None

    def check_deliverability(self) -> Zones:
        return self.get_zone()

    def get_zone(self) -> Zones:
        raise NotImplementedError()

    def is_valid(self) -> bool:
        raise NotImplementedError()

    def get_params_for_location(self) -> dict:
        raise NotImplementedError()

    def set_zone(self, request):
        if request.user.is_authenticated:
            user = request.user
            Location.objects.filter(user=user).update(is_active=False)
        else:
            user = None
        params = self.get_params_for_location()
        zone = self.get_zone()
        params['zone'] = zone
        if 'user' in params:
            del params['user']
        if 'is_active' in params:
            del params['is_active']
        location = Location.objects.create(**params, user=user, is_active=True if user else False)
        self.set_session(request, zone, location)
        return self.face(request)

    @staticmethod
    def get_previous_location(request):
        if request.session.get('location'):
            loc = Location.objects.filter(pk=request.session.get('location')).first()
            if loc:
                return loc
        if request.user.is_authenticated:
            return Location.objects.filter(user=request.user).order_by('-is_active', '-id').first()
        return None

    @staticmethod
    def get_location_util(request, location: Optional[Location] = None):
        if location is None:
            if request.session.get('location'):
                location = Location.objects.filter(pk=request.session.get('location')).select_related('zone').last()
            else:
                if not request.user.is_authenticated:
                    return
                location = Location.objects.filter(user=request.user).order_by('-is_active', '-id').first()
        return location

    @staticmethod
    def set_session(request, zone: Optional[Zones] = None, location: Optional[Location] = None) -> None:
        location = BaseZoneFacade.get_location_util(request, location)
        if zone is None and location is not None:
            zone = location.zone
        request.session['location'] = location.pk
        request.session['location_name'] = location.location_name or settings.DEFAULT_LOCATION_NAME
        if zone:
            request.session['zone'] = zone.pk
            request.session['zone_name'] = zone.name
        elif request.session.get('zone'):
            zone = Zones.objects.filter(id=request.session.get('zone')).first()
            request.session['zone_name'] = zone.name
        for MODE in settings.LOCATION_FETCHING_MODE_SET:
            attr_name = f'get_{MODE}_data'
            if hasattr(location, attr_name) and callable(getattr(location, attr_name)):
                request.session[MODE] = getattr(location, attr_name)()
            else:
                raise NotImplementedError(f'You have to implement {attr_name} at {Location} as "def {attr_name}(self) '
                                          f'-> dict:"')

    @staticmethod
    def face(request, location: Optional[Location] = None):
        location = BaseZoneFacade.get_location_util(request, location)
        infos = [not request.session.get(field) for field in ['zone', 'zone_name', 'location', 'location_name']]
        if any(infos):
            BaseZoneFacade.set_session(request, location=location)
        out = {
            "zone_id": request.session.get('zone'),
            "zone_name": request.session.get('zone_name'),
            "location_id": request.session.get('location'),
            "location_name": request.session.get('location_name'),
        }
        for MODE in settings.LOCATION_FETCHING_MODE_SET:
            attr_name = f'get_{MODE}_data'
            if location:
                if hasattr(location, attr_name) and callable(getattr(location, attr_name)):
                    out[MODE] = getattr(location, attr_name)()
                else:
                    raise NotImplementedError(
                        f'You have to implement {attr_name} at {Location} as "def {attr_name}(self) -> dict:"'
                    )
            else:
                out[MODE] = None
        return out


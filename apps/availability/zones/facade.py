from django.conf import settings

from apps.availability.base.facade import BaseZoneFacade
from apps.availability.models import Zones


class GeolocationFacade(BaseZoneFacade):

    def __init__(self, *args, **kwargs):
        super(GeolocationFacade, self).__init__(*args, **kwargs)
        self.zone_obj = Zones.objects.filter(zone__bbcontains=self.info_object).order_by('-id').first()

    def get_zone(self) -> Zones:
        return self.zone_obj

    def is_valid(self) -> bool:
        return self.zone_obj is not None

    def get_params_for_location(self) -> dict:
        return {
            'location': self.info_object,
            'location_name': settings.DEFAULT_LOCATION_NAME,
        }

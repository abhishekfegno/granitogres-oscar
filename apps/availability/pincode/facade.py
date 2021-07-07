from django.conf import settings
from oscar.core.loading import get_model

from apps.availability.base.facade import BaseZoneFacade
from apps.availability.models import Zones, PinCode


class PincodeFacade(BaseZoneFacade):

    def __init__(self, *args, **kwargs):
        super(PincodeFacade, self).__init__(*args, **kwargs)
        self._zone = None
        self.pin_object = PinCode.objects.filter(code=self.info_object).first()

    def get_zone(self) -> Zones:
        if self.pin_object and self._zone is None:
            zone_through = Zones.pincode.through.objects.filter(pincode=self.pin_object).first()
            self._zone = zone_through and zone_through.zones
        return self._zone

    def is_valid(self) -> bool:
        return self.pin_object is not None

    def get_params_for_location(self) -> dict:

        return {
            'pincode': self.info_object,
            'location_name': settings.DEFAULT_LOCATION_NAME,
        }

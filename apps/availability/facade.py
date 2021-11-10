from django.conf import settings


def get_facade():
    if settings.LOCATION_FETCHING_MODE == settings.PINCODE:
        from .pincode.facade import PincodeFacade
        return PincodeFacade
    if settings.LOCATION_FETCHING_MODE == settings.GEOLOCATION:
        from .zones.facade import GeolocationFacade
        return GeolocationFacade
    return None


ZoneFacade = get_facade()


def get_zone_from_pincode(_pincode):
    facade_object = ZoneFacade(_pincode)
    return facade_object.get_zone()

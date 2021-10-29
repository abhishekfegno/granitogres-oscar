from django.core.signing import Signer, BadSignature
from django.utils.deprecation import MiddlewareMixin
from django.utils.functional import lazy, SimpleLazyObject
from apps.availability.settings import *
from apps.availability.facade import ZoneFacade
from apps.users.models import Location


class CommonAvailabilityMiddleware(MiddlewareMixin):

    def process_request(self, request):
        """
        getting comma separated partner_ids from cookies.
        """
        # import pdb;pdb.set_trace()
        if not request.session.get('location') and request.user.is_authenticated:
            location = ZoneFacade.get_previous_location(request=request)
            if location:
                ZoneFacade.set_session(request=request, location=location)
        request.session['location'] = request.session.get('location', None)
        request.session['zone'] = zone = request.session.get('zone', None)


class AvailabilityZoneMiddleware(MiddlewareMixin):

    def process_request(self, request):
        pass
        # if settings.LOCATION_FETCHING_MODE == settings.GEOLOCATION:
        #     if not request.session.get('pincode') and request.user.is_authenticated:
        #
        # request.session['location'] = request.session.get('location', None)
        # request.session['zone'] = zone = request.session.get('zone', None)
        #
        # if str(request.path).startswith('/api/'):
        #     if (
        #             not zone
        #             and not request.session.get('location')
        #             and request.user.is_authenticated):
        #         location = Location.objects.filter(user=request.user).order_by('is_active', 'id').last()
        #     elif request.session.get('location'):
        #         location = Location.objects.filter(id=request.session.get('location')).last()
        #     else:
        #         location = None
        #
        #     if location:
        #         location_id = location.id
        #         zone_id = location.zone.id if location.zone else None
        #         location_coordinates = str(location.location)
        #         request.session['location'] = location_id
        #         request.session['location_coordinates'] = location_coordinates
        #         request.session['zone'] = zone_id
        #     if not location and request.user.is_authenticated:
        #         sa = request.user.default_shipping_address
        #         if sa and sa.location:
        #             zone = ZoneFacade(sa.location)
        #             is_available = zone.check_deliverability()
        #             if is_available:
        #                 zone.set_zone(request)

    # def process_response(self, request, response):
    #     response['X-Geo-Location-ID'] = request.session.get('location')
    #     response['X-Geo-Location-Point'] = request.session.get('location_coordinates')
    #     return response

from django.core.signing import Signer, BadSignature
from django.utils.deprecation import MiddlewareMixin
from django.utils.functional import lazy, SimpleLazyObject
from apps.availability.settings import *
from apps.users.models import Location


class AvailabilityPincodeMiddleware(MiddlewareMixin):

    def process_request(self, request):
        """
            getting comma separated partner_ids from cookies.
        """
        request.user.partner = SimpleLazyObject(
            lambda: getattr(request.user, 'profile') if hasattr(request.user, 'profile') else None
        )
        if not request.session.get('pincode') and request.user._profile and request.user._profile.pincode:
            request.session['pincode'] = request.user._profile.pincode.code


class AvailabilityZoneMiddleware(MiddlewareMixin):

    def process_request(self, request):
        request.session['location'] = request.session.get('location', None)
        request.session['zone'] = zone = request.session.get('zone', None)
        if str(request.path).startswith('/api/'):
            if (
                    not zone
                    and not request.session.get('location')
                    and request.user.is_authenticated):
                location = Location.objects.filter(user=request.user).order_by('is_active', 'id').last()
            elif request.session.get('location'):
                location = Location.objects.filter(id=request.session.get('location')).last()
            else: location = None
            print("Location : ", location)
            if location:
                location_id = location.id
                zone_id = location.zone.id if location.zone else None
                location_coordinates = str(location.location)
                request.session['location'] = location_id
                request.session['location_coordinates'] = location_coordinates
                request.session['zone'] = zone_id

    def process_response(self, request, response):
        response['X-Geo-Location-ID'] = request.session.get('location')
        response['X-Geo-Location-Point'] = request.session.get('location_coordinates')
        return response

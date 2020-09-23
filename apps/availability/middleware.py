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
        zone = request.session.get('zone', None)        # for scripting purpose.
        if not zone and request.user.is_authenticated:
            location = Location.objects.filter(user=request.user, is_active=True).only('id', 'zone').last()
            if location:
                location_id = location.id
                zone_id = location.zone_id
                request.session['location'] = location_id
                request.session['zone'] = zone_id
        else:
            request.session['location'] = request.session.get('location', None)
            request.session['zone'] = zone



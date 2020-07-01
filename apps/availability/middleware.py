from django.utils.deprecation import MiddlewareMixin
from django.utils.functional import lazy, SimpleLazyObject

def find_pincode_via_session(request):
        return request.user._profile.pincode.code


class AvailabilityMiddleware(MiddlewareMixin):

    def process_request(self, request):
        """
            getting comma separated partner_ids from cookies.
        """
        if request.user.is_authenticated:
            request.user._profile = SimpleLazyObject(
                lambda: getattr(request.user, 'profile') if hasattr(request.user, 'profile') else None
            )
            if not request.session.get('pincode') and request.user._profile.pincode:
                request.session['pincode'] = request.user._profile.pincode.code


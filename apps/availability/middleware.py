from django.utils.deprecation import MiddlewareMixin
from django.utils.functional import lazy, SimpleLazyObject


class AvailabilityMiddleware(MiddlewareMixin):

    def process_request(self, request):
        """
            getting comma separated partner_ids from cookies.
        """
        request.user.partner = SimpleLazyObject(
            lambda: getattr(request.user, 'profile') if hasattr(request.user, 'profile') else None
        )
        if not request.session.get('pincode') and request.user._profile and request.user._profile.pincode:
            request.session['pincode'] = request.user._profile.pincode.code


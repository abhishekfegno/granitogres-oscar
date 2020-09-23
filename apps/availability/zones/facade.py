from apps.availability.models import Zones
from apps.users.models import Location


class ZoneFacade(object):

    def check_deliverability(self, point):
        return Zones.objects.filter(zone__bbcontains=point).order_by('-id').first()

    def set_zone(self, request, zone, point):
        user = request.user if request.user.is_authenticated else None
        DEFAULT_LOCATION_NAME = "Deliverable"
        mgr = Location.objects
        if user:
            mgr.filter(user=user).update(is_active=False)
        params = {
            "location": point,
            "location_name": DEFAULT_LOCATION_NAME,
            "zone": zone
        }
        import pdb; pdb.set_trace()
        location = Location.objects.create(**params, user=user, is_active=True if user else False)
        request.session['location'] = location.id
        request.session['location_name'] = location.location_name or DEFAULT_LOCATION_NAME
        request.session['zone'] = zone.id
        request.session['zone_name'] = zone.name
        return self.face(request)

    def face(self, request):
        return {
            "zone_id": request.session.get('zone'),
            "zone_name": request.session.get('zone_name'),
            "location_id": request.session.get('location'),
            "location_name": request.session.get('location_name'),
            'location_coordinates': request.session.get('location_coordinates'),
        }

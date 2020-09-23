from apps.availability.models import Zones
from apps.users.models import Location


class ZoneFacade(object):

    def check_deliverability(self, point):
        return Zones.objects.filter(zone__bbcontains=point).order_by('-id').first()

    def set_zone(self, request, zone, point):
        user = request.user if request.user.is_authenticated else None
        location = None
        DEFAULT_LOCATION_NAME = "Deliverable"
        if user:
            params = {
                "location": point,
                "location_name": DEFAULT_LOCATION_NAME,
                "zone": zone
            }
            locations = Location.objects.filter(user=user)
            if locations.count() > 0:
                location = locations.last()
                locations.exclude(id=location.id).delete()
            elif locations:
                location = locations.get()
            else:
                location = Location.objects.create(**params, user=user)
            request.session['location'] = location.id
            request.session['location_coordinates'] = str(location.location)

        else:
            request.session['location'] = None
            request.session['location_coordinates'] = None

        request.session['zone'] = zone.id
        return {
            'zone': zone.name,
            'location': location.id if location else None,
            'location_name': location.location_name if location else DEFAULT_LOCATION_NAME,
            'location_coordinates': request.session.get('location_coordinates'),
        }




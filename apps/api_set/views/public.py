import pgeocode
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.api_set.serializers.public import ReturnReasonSerializer
from apps.dashboard.custom.models import ReturnReason

indian_pin_code_data = {}


def get_pin(country_code):
    global indian_pin_code_data
    indian_pin_code_data[country_code] = pgeocode.Nominatim(country_code)


@api_view(("GET",))
def return_reasons_list(request, *a, **kwargs):
    return Response(ReturnReasonSerializer(ReturnReason.objects.all(), many=True).data, status=200)


@api_view(("GET",))
def availability(request, *a, **kwargs):
    out = {}
    global indian_pin_code_data
    _pin_code = kwargs.get('pincode')
    if 'in' not in indian_pin_code_data:
        get_pin('in')
    pc = indian_pin_code_data['in'].query_postal_code(_pin_code)
    if pc['country code']:
        out = {
            'postal_code': '75013',
            'country code': "nan",
            'place_name': "nan",
            'state_name': "nan",
            'state_code': "nan",
            'county_name': "nan",
            'county_code': "nan",
            'community_name': "nan",
            'community_code': "nan",
            'latitude': "nan",
            'longitude': "nan",
            'accuracy': "nan"
        }
    return Response(out)

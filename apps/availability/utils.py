from django.conf import settings
from django.contrib.gis.geos import Point

from apps.availability.models import PinCode
import pgeocode

DEFAULT_PINCODE_KEY = 'pincode'


def load_all_postal_code_in_district(district):
    geo_india = pgeocode.Nominatim('IN')
    numpy_data = geo_india._data[(geo_india._data.county_name == district.name)].to_numpy()
    community = {}
    postal = {}

    for (country_code, postal_code, place_name, state_name, state_code, county_name,
         county_code, community_name, community_code, latitude, longitude, accuracy) in numpy_data:

        if community_name not in community.keys():

            community[community_name] = district.get_children().filter(name=district.name).first()

            if not community[community_name]:

                community[community_name] = district.add_child(
                    name=community_name, code=None
                )

        if postal_code not in postal.keys():

            postal[postal_code] = community[community_name].get_children().filter(code=postal_code).first()

            if not postal[postal_code]:

                postal[postal_code] = community[community_name].add_child(
                    name=place_name, code=postal_code, poly=Point(latitude, longitude)
                )









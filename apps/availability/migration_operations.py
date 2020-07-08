from django.db.transaction import atomic
from oscar.core.utils import slugify
from django.contrib.gis.geos import Point


@atomic
def populate_pincode(apps, schema_editor):
    import pgeocode
    geo_india = pgeocode.Nominatim('IN')
    from apps.availability.models import PinCode
    PinCode.objects.all().delete()
    root = PinCode.add_root(name="India", code=None)
    numpy_data = geo_india._data.to_numpy()
    state = {}
    district = {}
    community = {}
    postal = {}
    for (country_code, postal_code, place_name, state_name, state_code, county_name,
         county_code, community_name, community_code, latitude, longitude, accuracy) in numpy_data:

        print(f'Adding : {country_code} >> {state_name} >> {community_name}'
            # '\nconuntry_code :', country_code,
            # '\npostal_code :', postal_code,
            # '\nplace_name :', place_name,
            # '\nstate_name :', state_name,
            # '\nstate_code :', state_code,
            # '\ndistrict_name :', county_name,
            # '\ndistrict_code :', county_code,
            # '\ncommunity_name :', community_name,
            # '\ncommunity_code :', community_code,
            # '\nlatitude :', latitude,
            # '\nlongitude :', longitude,
            # '\naccuracy :', accuracy,
        )
        # state = {}
        # district = {}
        # community = {}
        # postal = {}

        if state_name not in state.keys():
            state[state_name] = root.get_children().filter(name=state_name).first()
            if not state[state_name]:
                state[state_name] = root.add_child(name=state_name, code=None)

        district_name = county_name
        if district_name not in district.keys():
            district[district_name] = state[state_name].get_children().filter(name=district_name).first()
            if not district[district_name]:
                district[district_name] = state[state_name].add_child(
                    name=district_name, code=None
                )

        # if community_name not in community.keys():
        #     community[community_name] = district[district_name].get_children().filter(name=county_name).first()
        #     if not community[county_name]:
        #         community[community_name] = district[district_name].add_child(
        #         name=community_name, code=None
        #         )

        # if postal_code not in postal.keys():
        #     postal[postal_code] = community[community_name].get_children().filter(name=county_name).first()
        #     if not postal[postal_code]:
        #         postal[postal_code] = community[community_name].add_child(
        #         name=place_name, code=postal_code, poly=Point(latitude, longitude)
        #         )


def populate_pincode_reverse(apps, schema_editor):
        from apps.availability.models import PinCode
        PinCode.objects.all().delete()

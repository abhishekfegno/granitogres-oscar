"""
PROJECT CONSTANTS AND WORKFLOW!!!


"""
# HAYSTACK_CONNECTIONS = {
#     'default': {
#         'ENGINE': 'haystack.backends.simple_backend.SimpleEngine',
#     },
# }


from django.contrib.gis.measure import D
STORES_GEODETIC_SRID = 4326
STORES_GEOGRAPHIC_SRID = 3577
STORES_MAX_SEARCH_DISTANCE = D(km=10)



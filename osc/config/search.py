import os
from collections import OrderedDict

from .base_dir import _is_env_set_as, BASE_DIR

# HAYSTACK_CONNECTIONS = {
#     'default': {
#         'ENGINE': os.environ.get('HAYSTACK_ENGINE', 'haystack.backends.simple_backend.SimpleEngine'),
#         'URL': os.environ.get('HAYSTACK_URL'),
#         'INCLUDE_SPELLING': _is_env_set_as('HAYSTACK_INCLUDE_SPELLING', True)
#     },
# }

# PRODUCTION SUPPORTED HAYSTACK

# HAYSTACK_CONNECTIONS = {
#     'default': {
#         'ENGINE': 'haystack.backends.solr_backend.SolrEngine',
#         'URL': 'http://127.0.0.1:8983/solr',
#         'INCLUDE_SPELLING': True,
#     },
# }


# THING WHICH WE GONNA USE.
HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.whoosh_backend.WhooshEngine',
        'PATH': os.path.join(BASE_DIR, 'whoosh-index'),
        'INCLUDE_SPELLING': True,
        'STORAGE': 'file',   # "ram|file"
    },
}


OSCAR_SEARCH_FACETS = {
    'fields': OrderedDict([
        ('product_class', {'name': 'Type', 'field': 'product_class'}),
        ('category', {'name': 'Category', 'field': 'category'}),
        ('title', {'name': 'Title', 'field': 'title'}),
    ]),
    'queries': OrderedDict([
        ('price_range',
         {
             'name': 'Price range',
             'field': 'price',
             'queries': [
                 # This is a list of (name, query) tuples where the name will
                 # be displayed on the front-end.
                 ('0 to 20', u'[0 TO 20]'),
                 ('20 to 40', u'[20 TO 40]'),
                 ('40 to 60', u'[40 TO 60]'),
                 ('60+', u'[60 TO *]'),
             ]
         }),
    ]),
}

# OSCAR_PRODUCT_SEARCH_HANDLER = None
# OSCAR_DASHBOARD_NAVIGATION # too long

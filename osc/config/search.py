import os

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
        'PATH': os.path.join(BASE_DIR, 'whoosh-index-file'),
        'INCLUDE_SPELLING': True,
    },
}


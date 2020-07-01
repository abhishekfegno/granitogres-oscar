import os

from .base_dir import _is_env_set_as

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': os.environ.get('HAYSTACK_ENGINE', 'haystack.backends.simple_backend.SimpleEngine'),
        'URL': os.environ.get('HAYSTACK_URL'),
        'INCLUDE_SPELLING': _is_env_set_as('HAYSTACK_INCLUDE_SPELLING', True)
    },
}

# PRODUCTION SUPPORTED HAYSTACK

# HAYSTACK_CONNECTIONS = {
#     'default': {
#         'ENGINE': 'haystack.backends.solr_backend.SolrEngine',
#         'URL': 'http://127.0.0.1:8983/solr',
#         'INCLUDE_SPELLING': True,
#     },
# }


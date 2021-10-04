import os
from .base_dir import BASE_DIR, _is_env_set_as

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_URL = '/assets/'
MEDIA_URL = '/src/'


STATIC_ROOT = os.path.join(BASE_DIR, "public", "static")
STATIC_DIR_MASTER = os.path.join(BASE_DIR, "public", "assets")
STATICFILES_DIRS = [STATIC_DIR_MASTER, ]
MEDIA_ROOT = os.path.join(BASE_DIR, 'public/media')

# INDEX_STATIC_ROOT = os.path.join(BASE_DIR, "public/reactAPI Supports multiple payments integration, though our system doesnot' well support this feature. (futurestic one.)_index_page/build/static")
#                                                           # special static root for index page build
# INDEX_STATIC_URL = os.path.join(BASE_DIR, "/static/")     # special static root for index page build

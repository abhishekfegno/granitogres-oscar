# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases
import os

from .base_dir import BASE_DIR, _is_env_set_as

# DATABASES = {
#     'default': {
#         'USER': '',
#         'PASSWORD': '',
#         'HOST': '',
#         'PORT': '',
#         'ATOMIC_REQUESTS': True,
#     }
# }
ENGINE = 'django.db.backends.sqlite3',
NAME = os.path.join(BASE_DIR, 'db.sqlite3'),

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',  # must use postgis
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST'),
        'PORT': 5432,
        'ATOMIC_REQUESTS': True,
    }
}

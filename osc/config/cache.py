CACHES = {
    'dummy': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'},
    'redis': {
        'BACKEND': 'django_redis.cache.RedisCache',
        "LOCATION": "redis://127.0.0.1:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            'server_max_value_length': 1024 * 1024 * 128,  # 128 MB
        },
        'TIMEOUT': 60 * 60 * 24 * 3,  # for 3 days
        'MAX_ENTRIES': 3000,          # 128 MB
        "KEY_PREFIX": "hauz_",
    },
    # 'memcached': {
    #     'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
    #     'LOCATION': '127.0.0.1:11211',
    # },
    'localmem': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    },
    'db': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'my_cache_table',
    },
    'filebased': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': '/tmp/django_cache',
    },
}
CACHE_MIDDLEWARE_ALIAS = 'redis'
CACHES['default'] = CACHES[CACHE_MIDDLEWARE_ALIAS]
# SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'

# CACHING

invalid_cache = False


# CACHE_MIDDLEWARE_SECONDS = 60 * 60 * 24 * 3  # 3 day
# CACHE_LONGEST_SECONDS = 60 * 60 * 24 * 30  # 30 days
#
# CACHE_COUNT_TIMEOUT = 60 * 60
# DEFAULT_CACHE_TTL = 60 * 30
# SOLO_CACHE = 'default'

CACHE_MIDDLEWARE_SECONDS = 5  # 5 sec
CACHE_LONGEST_SECONDS = 10  # 10 sec

CACHE_COUNT_TIMEOUT = 60
DEFAULT_CACHE_TTL = 10
SOLO_CACHE = 'default'

SOLO_CACHE_TIMEOUT = 60 * 60 * 24
THUMBNAIL_KVSTORE = 'sorl.thumbnail.kvstores.redis_kvstore.KVStore'





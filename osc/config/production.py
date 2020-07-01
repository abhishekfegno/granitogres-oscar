# PRODUCTION READY
from .base_dir import BASE_DIR, _is_env_set_as

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/


IN_PRODUCTION = _is_env_set_as('IN_PRODUCTION', True)
SECURE_HSTS_SECONDS = 60
SECURE_CONTENT_TYPE_NOSNIFF = IN_PRODUCTION
SECURE_BROWSER_XSS_FILTER = IN_PRODUCTION
SECURE_SSL_REDIRECT = IN_PRODUCTION
SESSION_COOKIE_SECURE = IN_PRODUCTION
SECURE_HSTS_PRELOAD = IN_PRODUCTION





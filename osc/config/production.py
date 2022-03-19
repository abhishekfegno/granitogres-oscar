# PRODUCTION READY
from .base_dir import BASE_DIR, _is_env_set_as

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/


IN_PRODUCTION = _is_env_set_as('IN_PRODUCTION', True)
SECURE_HSTS_SECONDS = 60
SECURE_CONTENT_TYPE_NOSNIFF = IN_PRODUCTION
SECURE_BROWSER_XSS_FILTER = IN_PRODUCTION
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = IN_PRODUCTION
SECURE_HSTS_PRELOAD = IN_PRODUCTION




import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn="https://470b51ff952d473dbd1d159a3ea0057c@o554636.ingest.sentry.io/6264926",
    integrations=[DjangoIntegration()],

    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production.
    traces_sample_rate=1.0,

    # If you wish to associate users to errors (assuming you are using
    # django.contrib.auth) you may enable sending PII data.
    send_default_pii=True
)

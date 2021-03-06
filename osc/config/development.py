from django.utils.functional import lazy

"""
LIST_PRODUCT_CHILD_ONLY = True displays only 'standalone' and 'child' products in 
                        product listing and will show child directly in detailed view
"""
LIST_PRODUCT_CHILD_ONLY = True


DEBUG_TOOLBAR_PANELS = (
    # Defaults
    'debug_toolbar.panels.versions.VersionsPanel',
    'debug_toolbar.panels.timer.TimerPanel',
    'debug_toolbar.panels.settings.SettingsPanel',
    'debug_toolbar.panels.headers.HeadersPanel',
    'debug_toolbar.panels.request.RequestPanel',
    'debug_toolbar.panels.sql.SQLPanel',
    'debug_toolbar.panels.staticfiles.StaticFilesPanel',
    'debug_toolbar.panels.templates.TemplatesPanel',
    'debug_toolbar.panels.cache.CachePanel',
    'debug_toolbar.panels.signals.SignalsPanel',
    'debug_toolbar.panels.logging.LoggingPanel',
    'debug_toolbar.panels.redirects.RedirectsPanel',
    # Additional
    # 'elastic_panel.panel.ElasticDebugPanel',
)


AUTHENTICATION_BACKENDS = (
    'oscar.apps.customer.auth_backends.EmailBackend',
    'django.contrib.auth.backends.ModelBackend',
)


INTERNAL_IPS = [
    '127.0.0.1',
    'localhost',
    'localhost:8000',
    '192.168.1.100',
    'grocery.dev.fegno.com',
    'abchauz.dev.fegno.com',
]


ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_VERIFICATION = 'optional'
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_EMAIL_CONFIRMATION_ANONYMOUS_REDIRECT_URL = '/email-verification/done/?verification=1'
ACCOUNT_EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL = '/email-verification/done/?verification=1'

ACCOUNT_EMAIL_SUBJECT_PREFIX = "[Grocery] "

SITE_ID = 1

# #SAMESITE
# CSRF_COOKIE_SECURE = True
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SAMESITE = 'None'
# SESSION_COOKIE_SAMESITE = 'None'
#
# DCS_SESSION_COOKIES_SAMESITE = 'None'
# CORS_ALLOW_CREDENTIALS = "True"
# CORS_ALLOW_HEADERS = "Content-Type"
# CORS_ALLOW_METHODS = "True"
# CORS_PREFLIGHT_MAX_AGE = 86400


# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
# EMAIL_HOST = 'smtp.sendgrid.net'
# EMAIL_PORT = 587
# EMAIL_HOST_USER = 'testsite_app'
# EMAIL_HOST_PASSWORD = 'mys3cr3tp4ssw0rd'
# EMAIL_USE_TLS = True
# DEFAULT_FROM_EMAIL = 'TestSite Team <noreply@example.com>'

REST_SESSION_LOGIN = True


EMAIL_BACKEND = "sgbackend.SendGridBackend"
SENDGRID_API_KEY = "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"
DEFAULT_FROM_EMAIL = 'abchauzdigital@gmail.com'
"""
password: adminabchauz@303
"""


FEATURED_CATEGORY_SLUG = 'featured'

DEFAULT_PAGE_SIZE = 12

MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

COOKIE_STORAGE_PINCODE_KEY = 'pincode'

FN_LOAD_PINCODE_FOR_USER = lazy(lambda request: (
        request.user.is_authenticated and
        request.user._profile and
        request.user._profile.pincode and
        request.user._profile.pincode.code
))
LOAD_INITIAL_COUNTRIES = ('IN', )


MOBILE_NUMBER_VALIDATOR = {
    'LENGTH': 10
}
OTP_LENGTH = 4


# GOOGLE_MAPS_API_KEY = 'AIzaSyDS7nukrr2rQnvedbjoUF81sSXYc1ZlEXI'
GOOGLE_MAPS_API_KEY = 'AIzaSyD1UdcNK1QybgaG5Hrzb-1xVFhy8CrMkjk'
STORES_GEOGRAPHIC_SRID = 3577
STORES_GEODETIC_SRID = 4326
# STORES_MAX_SEARCH_DISTANCE = ''

USER_ADDRESS = {
    'COUNTRY': 'IN',
}

DEFAULT_PERIOD_OF_RETURN = {'minutes': 180}

WIDE_SCREEN_BANNER_IMAGE_SIZE = '1920x503'
SHORT_SCREEN_BANNER_IMAGE_SIZE = '312x312'
WIDE_SCREEN_BANNER_THUMBNAIL_SIZE = '192x50'
SHORT_SCREEN_BANNER_THUMBNAIL_SIZE = '3x3'

THUMBNAIL_PRESERVE_FORMAT = True

NEED_LOCATION_ON_ADDRESS_SAVING = False

TIME_SLOT_ENABLED = False

CKEDITOR_UPLOAD_PATH = "cms/"
CKEDITOR_IMAGE_BACKEND = 'pillow'
CKEDITOR_RESTRICT_BY_USER = True
CKEDITOR_BROWSE_SHOW_DIRS = False

CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'full',
        'height': 700,
        'width': 'auto',
        'uiColor': '#f4f5f7',

    },
}






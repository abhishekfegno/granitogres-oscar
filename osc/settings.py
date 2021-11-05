"""
Django settings for osc project.

Generated by 'django-admin startproject' using Django 3.0.5.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""

import os
from dotenv import load_dotenv
from .config.base_dir import BASE_DIR

load_dotenv()

SECRET_KEY = '@sjw(#19ix-we_-0ijndhsw4x)53vccyxx%y0xl4u$tsr*&h5b'

ALLOWED_HOSTS = ['*']

DEBUG = True

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.flatpages',
    'django.contrib.gis',
    'django.contrib.postgres',
    'django.contrib.humanize',

    # 'stores',
    # 'stores.dashboard',

    'apps.users',
    # 'apps.api_set',
    'apps.api_set_v2',
    'apps.api_set.apps.ApiSetConfig',
    'apps.mod_oscarapi.apps.ModOscarapiConfig',
    'apps.logistics.apps.LogisticsConfig',
    'apps.buynow.apps.BuyNowConfig',

    'oscar',
    'apps.address.apps.AddressConfig',
    'apps.basket.apps.BasketConfig',
    'apps.customer.apps.CustomerConfig',
    'apps.partner.apps.PartnerConfig',
    'apps.payment.apps.PaymentConfig',
    'apps.availability.apps.AvailabilityConfig',
    'apps.catalogue.reviews.apps.CatalogueReviewsConfig',
    'apps.catalogue.apps.CatalogueConfig',

    # 'apps.dashboard.ranges',
    'apps.dashboard.ranges.apps.RangesDashboardConfig',
    'apps.dashboard.custom.apps.CustomConfig',
    'apps.dashboard.catalogue',
    # 'apps.dashboard.orders',
    'apps.dashboard.orders.apps.OrdersDashboardConfig',

    # 'apps.dashboard.communications.apps.CommunicationsDashboardConfig',


    # 'apps.dashboard.catalogue.apps.CatalogueDashboardConfig',
    'apps.dashboard.users.apps.UsersDashboardConfig',
    'apps.checkout.apps.CheckoutConfig',
    'apps.search.apps.SearchConfig',
    'apps.order.apps.OrderConfig',
    'apps.shipping.apps.ShippingConfig',
    'apps.rfq.apps.RfqConfig',


    'oscar.apps.analytics.apps.AnalyticsConfig',
    # 'oscar.apps.address.apps.AddressConfig',
    'oscar.apps.offer.apps.OfferConfig',
    'oscar.apps.voucher.apps.VoucherConfig',
    'oscar.apps.wishlists.apps.WishlistsConfig',


    'oscar.apps.dashboard.apps.DashboardConfig',
    'oscar.apps.dashboard.reports.apps.ReportsDashboardConfig',
    # 'oscar.apps.dashboard.orders.apps.OrdersDashboardConfig',
    'oscar.apps.dashboard.offers.apps.OffersDashboardConfig',
    'oscar.apps.dashboard.partners.apps.PartnersDashboardConfig',
    'oscar.apps.dashboard.pages.apps.PagesDashboardConfig',
    # 'oscar.apps.dashboard.ranges.apps.RangesDashboardConfig',
    'oscar.apps.dashboard.reviews.apps.ReviewsDashboardConfig',
    'oscar.apps.dashboard.vouchers.apps.VouchersDashboardConfig',
    'oscar.apps.dashboard.communications.apps.CommunicationsDashboardConfig',
    'oscar.apps.dashboard.shipping.apps.ShippingDashboardConfig',

    'allauth',
    'allauth.account',

    'rest_auth',
    'rest_auth.registration',
    'django_filters',
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_gis',
    'drf_extra_fields',

    'oscarapi',
    'oscarapicheckout',

    'oscar_accounts.apps.AccountsConfig',
    'oscar_accounts.dashboard.apps.AccountsDashboardConfig',

    # third PArty
    'floppyforms',
    'colorfield',
    'taggit',

    #CORS
    'corsheaders',

    # 3rd-party apps that oscar depends on
    'widget_tweaks',
    'haystack',
    'treebeard',
    'sorl.thumbnail',
    'django_tables2',

    'debug_toolbar',
    'elastic_panel',
    'django_extensions',
    'push_notifications',
    'ckeditor',



]

MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',

    # BUILTINS
    'django.middleware.security.SecurityMiddleware',
    # 'django.contrib.sessions.middleware.SessionMiddleware',

    # #Custom session middleware
    'apps.api_set_v2.middleware.CustomSessionMiddleware',

    # #cors middleware
    'corsheaders.middleware.CorsMiddleware',

    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # HANDS_ON
    'apps.availability.middleware.AvailabilityZoneMiddleware',      # must be before basket middleware
    'lib.middlewares.BypassCSRF',

    # THIRD PARTY
    'apps.basket.middleware.BasketMiddleware',          # over-rided Basket middleware of oscar
    'oscarapi.middleware.ApiBasketMiddleWare',
    # 'oscarapi.middleware.HeaderSessionMiddleware',
    # 'oscarapi.middleware.ApiGatewayMiddleWare',



    # Enforced Response Modifiers
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',
    'debug_toolbar_force.middleware.ForceDebugToolbarMiddleware',

]


CORS_ALLOWED_ORIGINS = [
    'http://127.0.0.1:8000',
    'http://127.0.0.1:3000',
    'http://dev.fegno.com:3000',
    'https://localhost:3000',
    'https://dev.fegno.com:3000',
    'http://dev.fegno.com:3000',
    'http://localhost:3000',
]

CORS_ORIGIN_ALLOW_ALL = True

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]
CORS_ORIGIN_WHITELIST = (
   'http://localhost:3000',
)

ROOT_URLCONF = 'osc.urls'
WSGI_APPLICATION = 'osc.wsgi.application'
ASGI_APPLICATION = 'osc.asgi.application'


"""
LOCATION_FETCHING_MODE = 'geolocation'
The Working mode is configured on osc.config.oscar.LOCATION_FETCHING_MODE
so that we can manage oscar dashboard also from there.
"""



SITE_ID = 1

AUTH_USER_MODEL = 'users.User'

from .config.cache import *                 # noqa: F401,F404
from .config.database import *              # noqa: F401,F404
from .config.default import *               # noqa: F401,F404
from .config.development import *           # noqa: F401,F404
from .config.drf import *                   # noqa: F401,F404
# from .config.elastic import *             # noqa: F401,F404
from .config.oscar import *                 # noqa: F401,F404
from .config.payments import *              # noqa: F401,F404
from .config.push_notifications import *    # noqa: F401,F404
from .config.production import *            # noqa: F401,F404
from .config.project import *               # noqa: F401,F404
from .config.route import *                 # noqa: F401,F404
from .config.search import *                # noqa: F401,F404
from .config.sms import *                   # noqa: F401,F404
from .config.static import *                # noqa: F401,F404
from .config.templates import *             # noqa: F401,F404

DATA_UPLOAD_MAX_MEMORY_SIZE = 62914560  # 60MB
OSCAR_SAVE_SENT_EMAILS_TO_DB = True

"""
Email : grocery@gmail.com
Password : globalfurnimart@456
Mobile : 9497270863
DOB : 18-05-1995
"""




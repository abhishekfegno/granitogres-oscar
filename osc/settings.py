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

    # 'stores',
    # 'stores.dashboard',

    'apps.users',
    'apps.api_set.apps.ApiSetConfig',
    'apps.mod_oscarapi.apps.ModOscarapiConfig',
    'django_oscar_buy_now_api.apps.BuyNowConfig',

    'oscar',
    'apps.basket.apps.BasketConfig',
    'apps.customer.apps.CustomerConfig',
    'apps.partner.apps.PartnerConfig',
    'apps.payment.apps.PaymentConfig',
    'apps.availability.apps.AvailabilityConfig',
    'apps.catalogue.apps.CatalogueConfig',
    'apps.dashboard.custom.apps.CustomConfig',
    'apps.dashboard.users.apps.UsersDashboardConfig',
    'apps.dashboard.catalogue',
    'apps.checkout.apps.CheckoutConfig',
    'apps.search.apps.SearchConfig',

    'oscar.apps.analytics.apps.AnalyticsConfig',
    'oscar.apps.address.apps.AddressConfig',
    'oscar.apps.shipping.apps.ShippingConfig',
    'oscar.apps.offer.apps.OfferConfig',
    'oscar.apps.order.apps.OrderConfig',
    'oscar.apps.voucher.apps.VoucherConfig',
    'oscar.apps.wishlists.apps.WishlistsConfig',
    'oscar.apps.catalogue.reviews.apps.CatalogueReviewsConfig',

    'oscar.apps.dashboard.apps.DashboardConfig',
    'oscar.apps.dashboard.reports.apps.ReportsDashboardConfig',
    'oscar.apps.dashboard.orders.apps.OrdersDashboardConfig',
    'oscar.apps.dashboard.offers.apps.OffersDashboardConfig',
    'oscar.apps.dashboard.partners.apps.PartnersDashboardConfig',
    'oscar.apps.dashboard.pages.apps.PagesDashboardConfig',
    'oscar.apps.dashboard.ranges.apps.RangesDashboardConfig',
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

    'oscarapi',
    'oscarapicheckout',

    'oscar_accounts.apps.AccountsConfig',
    'oscar_accounts.dashboard.apps.AccountsDashboardConfig',

    # third PArty
    'floppyforms',

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

]


MIDDLEWARE = [
    # BUILTINS
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # HANDS_ON
    # 'apps.availability.middleware.AvailabilityMiddleware',      # mist be before basket middleware
    'lib.middlewares.BypassCSRF',

    # THIRD PARTY
    'apps.basket.middleware.BasketMiddleware',          # over-rided Basket middleware of oscar
    'oscarapi.middleware.ApiBasketMiddleWare',
    # 'oscarapi.middleware.HeaderSessionMiddleware',
    # 'oscarapi.middleware.ApiGatewayMiddleWare',

    # Enforced Response Modifiers
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',
    # 'debug_toolbar_force.middleware.ForceDebugToolbarMiddleware',

]


ROOT_URLCONF = 'osc.urls'
WSGI_APPLICATION = 'osc.wsgi.application'
ASGI_APPLICATION = 'osc.asgi.application'


SITE_ID = 1

AUTH_USER_MODEL = 'users.User'

from .config.cache import *
from .config.database import *
from .config.default import *
from .config.development import *
from .config.drf import *
# from .config.elastic import *
from .config.oscar import *
from .config.payments import *
from .config.production import *
from .config.project import *
from .config.route import *
from .config.search import *
from .config.sms import *
from .config.static import *
from .config.templates import *

"""
Email : woodncart@gmail.com
Password : globalfurnimart@456
Mobile : 9497270863
DOB : 18-05-1995
"""




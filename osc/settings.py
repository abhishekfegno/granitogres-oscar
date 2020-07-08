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


    'oscar',
    'django_oscar_buy_now_api',
    'apps.basket.apps.BasketConfig',
    'apps.availability.apps.AvailabilityConfig',
    'apps.catalogue.apps.CatalogueConfig',
    'apps.dashboard.custom.apps.CustomConfig',
    'apps.dashboard.users.apps.UsersDashboardConfig',
    'apps.dashboard.catalogue',
    'apps.checkout.apps.CheckoutConfig',
    # 'apps.dashboard.catalogue.apps.CatalogueDashboardConfig',

    'oscar.apps.analytics',
    'oscar.apps.address',
    'oscar.apps.shipping',
    'oscar.apps.catalogue.reviews',
    'oscar.apps.partner',
    'oscar.apps.payment',
    'oscar.apps.offer',
    'oscar.apps.order',
    'oscar.apps.customer',
    'oscar.apps.search',
    'oscar.apps.voucher',
    'oscar.apps.wishlists',
    'oscar.apps.dashboard',
    'oscar.apps.dashboard.reports',
    'oscar.apps.dashboard.orders',
    'oscar.apps.dashboard.offers',
    'oscar.apps.dashboard.partners',
    'oscar.apps.dashboard.pages',
    'oscar.apps.dashboard.ranges',
    'oscar.apps.dashboard.reviews',
    'oscar.apps.dashboard.vouchers',
    'oscar.apps.dashboard.communications',
    'oscar.apps.dashboard.shipping',
    # 'oscar.apps.catalogue',
    # 'oscar.apps.checkout.apps.CheckoutConfig',
    # 'oscar.apps.dashboard.users',
    # 'oscar.apps.dashboard.catalogue',

    'apps.users',
    'apps.api_set',
    'apps.mod_oscarapi',

    'allauth',
    'allauth.account',

    'rest_auth',
    'rest_auth.registration',

    'django_filters',

    'rest_framework',
    'rest_framework.authtoken',

    'oscarapi',
    'oscarapicheckout',

    'oscar_accounts.apps.AccountsConfig',
    'oscar_accounts.dashboard.apps.AccountsDashboardConfig',

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

    # Django Elasticsearch integration
    # 'django_elasticsearch_dsl',

    # Django REST framework Elasticsearch integration (this package)
    # 'django_elasticsearch_dsl_drf',

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
    'apps.availability.middleware.AvailabilityMiddleware',      # mist be before basket middleware
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

# AUTH_USER_MODEL = 'users.User'

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




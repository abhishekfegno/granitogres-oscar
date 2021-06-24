
# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators
import os
from .base_dir import *

AUTH_PASSWORD_VALIDATORS = [
    # {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    # {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    # {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_L10N = True
USE_TZ = True

SITE_ID = 1


VAPID_HEADER = {"Authorization": "vapid t=eyJ0eXAiOiJKV1QiLCJhbGciOiJFUzI1NiJ9.eyJhdWQiOiJodHRwczovL2FuZHJvaWQuZ29vZ2xlYXBpcy5jb20iLCJleHAiOiIxNTkyMzY0OTgwIiwic3ViIjoibWFpbHRvOiBqZXJpbmlzcmVhZHlAZ21haWwuY29tIn0.2Alh247fIyVh0dCbKjvjfJSYCFzYANlURi0ro6igDHkxcIoFOFE1Soui-2DyEcBzXrrFrQ5WvWmYkq7uTTSbvA,k=BEl5jwQO2JYxzaUExbJRF5zlmLs7cOnQ5o0b90W7ZNwK1U8yz_b7th8s5XHD4Mrfl9oMj9IsDXlsq7lOjMAV0Ck"}
VAPID_APPLICATION_SERVER_KEY = "BEl5jwQO2JYxzaUExbJRF5zlmLs7cOnQ5o0b90W7ZNwK1U8yz_b7th8s5XHD4Mrfl9oMj9IsDXlsq7lOjMAV0Ck"




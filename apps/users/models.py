# /home/jk/code/grocery/apps/users/models.py

from datetime import timedelta, datetime

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.gis.db.models import PointField
from django.db import models
from random import randint

from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone
from oscar.core.compat import get_user_model

from apps.api_set import app_settings
from apps.users.manager import ActiveOTPManager
from apps.users.validators import UnicodeMobileNumberValidator
from lib.utils.sms import send_otp


class User(AbstractUser):
    username_validator = UnicodeMobileNumberValidator()
    REQUIRED_FIELDS = ['email']

    username = models.CharField(
        'mobile',
        max_length=10,
        unique=True,
        help_text='Required. Your 10 digit Mobile number.',
        validators=[UnicodeMobileNumberValidator()],
        error_messages={
            'unique': "This mobile number already exists.",
        },
    )

    @property
    def mobile(self):
        return self.username

    @mobile.setter
    def mobile(self, mobile):
        self.username = mobile

    @property
    def otp(self):
        return hasattr(self, '_otp') and self._otp or None

    def get_short_name(self):
        return self.first_name or self.last_name or self.username


class Location(models.Model):
    location = PointField()
    location_name = models.CharField(max_length=90)
    is_active = models.BooleanField(default=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    zone = models.ForeignKey('availability.Zones', on_delete=models.SET_NULL, null=True, blank=True)

    @property
    def partner(self):
        if self.zone:
            return self.zone.partner

    def save(self, *args, **kwargs):
        super(Location, self).save(*args, **kwargs)


class OTP(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                             related_name='otp_set', null=True, blank=True)
    mobile_number = models.CharField(
        validators=[UnicodeMobileNumberValidator()],
        max_length=10,
    )
    code = models.CharField(max_length=6)
    is_active = models.BooleanField(default=True)
    no_of_times_send = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(blank=True)

    active = ActiveOTPManager()

    @property
    def user_profile(self):
        return self.user

    @user_profile.setter
    def user_profile(self, user):
        self.user = user

    @property
    def is_verified(self):
        return not self.is_active

    @is_verified.setter
    def is_verified(self, value):
        self.is_active = not bool(value)

    @classmethod
    def generate(cls, mobile):
        User = get_user_model()
        otp = cls(mobile_number=mobile)
        otp.code = f'{randint(app_settings.OTP_MIN_VALUE, app_settings.OTP_MAX_VALUE)}'
        otp.user = User.objects.filter(username=mobile).first()
        otp.save()
        return otp

    def send_message(self):
        if app_settings.MOBILE_NUMBER_VALIDATOR['MAX_RETRIES'] > self.no_of_times_send:
            self.no_of_times_send += 1
            status = send_otp(phone_no=self.mobile_number, otp=self.code)   # returns a bool
            if status:
                self.save()
            return status

    @property
    def valid_upto(self):
        return self.created_at + timedelta(seconds=app_settings.OTP_EXPIRY)

    @property
    def is_valid(self):
        return self.is_active and (self.created_at + timedelta(seconds=app_settings.OTP_EXPIRY) > timezone.now())

    @classmethod
    def validate(cls, **kwargs):
        from django.utils import timezone
        otp = cls.objects.filter(**kwargs,
                                 created_at__gt=(timezone.now()-timedelta(seconds=app_settings.OTP_EXPIRY))).last()
        if otp:
            otp.is_verified = True
            otp.save()
        return otp

    def save(self, *args, **kwargs):
        if not self.pk:
            self.created_at = datetime.now()
        return super(OTP, self).save(*args, **kwargs)

    objects = models.Manager()

    def generate_user(self):
        if self.is_active:
            raise Exception('user cannot be verified before otp verification getting completed!')
        if self.user:
            raise Exception('User with this Mobile number already exists!')
        if User.objects.filter(username=self.mobile_number).exists():
            raise Exception('User with this Mobile number already exists!')

        self.user = User.objects.create_user(
            username=self.mobile_number
        )
        self.user.set_unusable_password()
        self.user.save()
        self.save()
        return self.user


@receiver(pre_save, sender=User)
def update_email(sender, instance, **kwargs):
    if not instance.email:
        instance.email = f"{instance.username}@grocery.app"



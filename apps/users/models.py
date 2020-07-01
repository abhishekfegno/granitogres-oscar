
# Create your models here.
from datetime import timedelta, datetime

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.cache import cache
from django.db import models
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from oscar.core.compat import get_user_model
from random import randint
from lib import cache_key
from lib.cache import cache_library
from lib.utils.sms import send_otp

User = get_user_model()
OTP_EXPIRY = getattr(settings, 'OTP_EXPIRY', 1500)


class UserProfile(models.Model):
    GST_CACHE_KEY = cache_key.gst_in__cache_key
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, related_name='profile')
    gst_number = models.CharField(max_length=32, unique=True, null=True, blank=True)
    name = models.CharField(max_length=32, null=True, )
    mobile = models.CharField(max_length=12, unique=True, null=True)
    email = models.CharField(max_length=32, unique=True, null=True, blank=True)
    pincode = models.ForeignKey('availability.PinCode', on_delete=models.SET_NULL, null=True, blank=True)

    @classmethod
    def get_gst(cls, user):
        _user_id = user.id
        data = cache.get(GSTNumber.GST_CACHE_KEY, {})
        gst = data.get(_user_id, ...)   # using ellipsis instead of None as 'key_not_found' case identifier
        if gst and gst is not ...:
            return gst
        # only one time for a user
        has_gst = hasattr(user, 'gst')
        gst = user.gst.gst_number if has_gst else None
        data[_user_id] = gst
        cache.set(GSTNumber.GST_CACHE_KEY, data)
        return gst


@receiver(pre_save, sender=User)
def update_email_as_username(sender, instance, **kwargs):
    if sender == User:
        instance.username = instance.email


@receiver(post_save, sender=UserProfile)
def update_gst_on_cache(sender, instance, **kwargs):
    data = cache.get(sender.GST_CACHE_KEY, {})
    data[instance.user_id] = instance.gst_number
    cache.set(sender.GST_CACHE_KEY, data)


class OTP(models.Model):
    user_profile = models.OneToOneField('users.UserProfile', on_delete=models.CASCADE, related_name='otp')
                                                                        # We need not need to be log all the otp's.
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(blank=True)

    @classmethod
    def generate(cls, user_profile):
        if hasattr(user_profile, 'otp'):
            otp = user_profile.otp
            old_otp = otp.code
            otp.code = f'{randint(100000, 999999)}'
            while old_otp == otp.code:
                # avoid any case of otp duplication
                # Wont enter this loop 99.99% cases
                otp.code = f'{randint(100000, 999999)}'
        else:
            otp = cls(user_profile=user_profile, code=f'{randint(100000, 999999)}')
        otp.save()
        return otp

    def send_message(self):
        return send_otp(phone_no=self.user_profile.mobile, otp=str(self.code))

    @property
    def valid_upto(self):
        return self.created_at + timedelta(seconds=settings.OTP_EXPIRY)

    @classmethod
    def validate(cls, **kwargs):
        from django.utils import timezone
        otp = cls.objects.filter(**kwargs, created_at__gt=(timezone.now()-timedelta(seconds=settings.OTP_EXPIRY))).last()
        return getattr(otp, 'user_profile') if otp else None

    def save(self, *args, **kwargs):
        if not self.pk:
            self.created_at = datetime.now()
        return super(OTP, self).save(*args, **kwargs)


GSTNumber = UserProfile     # backward Compatability

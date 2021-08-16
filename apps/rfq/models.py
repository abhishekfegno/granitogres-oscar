import random

from django.conf import settings
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

from lib.utils.sms import send_otp


class RFQ(models.Model):
    basket = models.ForeignKey('basket.Basket', on_delete=models.SET_NULL, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    mobile_number = PhoneNumberField(max_length=255, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    otp = models.CharField(null=True, max_length=6)
    pincode = models.CharField(max_length=8)

    @classmethod
    def convert_from_basket(cls, basket, user=None, name=None, mobile_number=None, pincode=None):
        basket.freeze()
        _user = user or basket.user
        if _user and not name:
            name = _user.get_full_name()
            mobile_number = _user.mobile

        enq = cls.objects.create(
            basket=basket,
            user=user or basket.user,
            name=name,
            mobile_number=mobile_number,
            otp=str(random.randint(1000, 9999)),
            pincode=pincode
        )
        enq.send_otp()

    def send_otp(self):
        send_otp(str(self.mobile_number), self.otp)

    @classmethod
    def verify(cls, pk, otp):
        instance = cls.objects.filter(pk=pk, otp=otp).first()
        if instance:
            instance.is_verified = True
            instance.save()
            return instance



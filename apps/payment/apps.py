import oscar.apps.payment.apps as apps
from django.db.models.signals import post_save


class PaymentConfig(apps.PaymentConfig):
    name = 'apps.payment'

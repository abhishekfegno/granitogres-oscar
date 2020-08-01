from django.conf import settings
from django.db import models
from oscar.apps.payment.models import *  # noqa isort:skip
from rest_framework.fields import HStoreField


class PaymentGateWayResponse(models.Model):
    PURCHASE = 'Purchase'
    REFUND = 'Refund'
    OTHERS = 'Others'

    transaction_id = models.CharField(max_length=128, name="Payment Transaction ID")
    transaction_type = models.CharField(max_length=128, choices=(
        (PURCHASE, PURCHASE),
        (REFUND, REFUND),
        (OTHERS, OTHERS),
    ), default=PURCHASE)
    source = models.ForeignKey('payment.Source', on_delete=models.PROTECT)
    amount = models.FloatField()
    _response = HStoreField()
    payment_status = models.BooleanField()
    payee = models.ForeignKey(settings.AUTH_USER_MODEL,  on_delete=models.PROTECT)
    description = models.TextField(null=True, blank=True)
    parent_transaction = models.ForeignKey('self', on_delete=models.PROTECT, null=True, blank=True)

    def __str__(self):
        return self.transaction_id




# class CODRecords(models.Model):
#     order = models.ForeignKey('payment.Order', on_delete=models.PROTECT)
#     order_assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
#     created_on = models.DateTimeField()
#
#
#
#
#

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
    # payee = models.ForeignKey(settings.AUTH_USER_MODEL,  on_delete=models.PROTECT)
    description = models.TextField(null=True, blank=True)
    parent_transaction = models.ForeignKey('self', on_delete=models.PROTECT, null=True, blank=True)

    def __str__(self):
        return self.transaction_id


    # Concept of payee is depricated and will be removed soon.
    _payee = None

    def get_payee(self):
        return self._payee

    def set_payee(self, value):
        self._payee = value

    payee = property(get_payee, set_payee)

class COD(models.Model):

    order = models.OneToOneField('order.Order', on_delete=models.PROTECT, related_name='cod')
    amount = models.FloatField()
    created_on = models.DateTimeField()
    cod_accepted = models.BooleanField(default=False)
    cod_transferred = models.BooleanField(default=False)
    amount_received_on = models.DateTimeField(null=True, blank=True)

    def amount_to_receive(self):
        if not self.amount_received_on:
            return float(self.amount) - float(self.cod_refunds.aggregate(net_amt=models.Sum('amount'))['net_amt'] or 0)


class CODRepayments(models.Model):
    cod = models.ForeignKey(COD, on_delete=models.PROTECT, related_name='cod_refunds')
    amount = models.DecimalField(max_digits=16, decimal_places=2 )
    amount_received_on = models.DateTimeField(null=True, blank=True)

    @property
    def cod_response(self):
        return {
            'id': 'COD-0000-' + str(self.id),
            'amount': self.amount,
            'type': 'cod',
            'collection_state': self.cod.cod_accepted,
            'collection_transfer_state': self.cod.cod_transferred,
            'transaction_date': self.amount_received_on,
        }

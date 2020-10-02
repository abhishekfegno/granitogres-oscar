
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.functional import cached_property
from django.contrib.postgres.fields import HStoreField
from oscar.apps.payment import abstract_models


class SourceManager(models.Manager):

    def get_queryset(self):
        return super(SourceManager, self).get_queryset().filter(is_active=True)


class Source(abstract_models.AbstractSource):
    is_active = models.BooleanField(default=True)

    objects = SourceManager()
    all = models.Manager()


from oscar.apps.payment.models import *  # noqa isort:skip


class PaymentGateWayResponse(models.Model):
    PURCHASE = 'Purchase'
    REFUND = 'Refund'
    OTHERS = 'Others'

    transaction_id = models.CharField(max_length=128, null=True, verbose_name="Payment Transaction ID")
    transaction_type = models.CharField(max_length=128, choices=(
        (PURCHASE, PURCHASE),
        (REFUND, REFUND),
        (OTHERS, OTHERS),
    ), default=PURCHASE)
    source = models.ForeignKey('payment.Source', on_delete=models.PROTECT)
    amount = models.FloatField()
    response = HStoreField(null=True)
    payment_status = models.BooleanField()
    # payee = models.ForeignKey(settings.AUTH_USER_MODEL,  on_delete=models.PROTECT)
    description = models.TextField(null=True, blank=True)
    parent_transaction = models.ForeignKey('self', on_delete=models.PROTECT, null=True, blank=True)

    def __str__(self):
        return f"{self.transaction_type} of {self.amount} " + (
            f"with transaction id #{self.transaction_id}" if self.transaction_id else ''
        )


class COD(models.Model):
    """
    COD Model acts as a seperate Gateway for Accounts. Entry To this Model assumes User had paid amount to
    ecommerce Business, but in credit! on time of delivery, Delivery Boys can refer this model to Calculate
    the amount to be collected.
    For Refund Procedure, Refunds will be generated across COD's
    """
    order = models.OneToOneField('order.Order', on_delete=models.PROTECT, related_name='cod')
    amount = models.FloatField()
    created_on = models.DateTimeField()
    cod_accepted = models.BooleanField(default=False)
    cod_transferred = models.BooleanField(default=False)
    amount_received_on = models.DateTimeField(null=True, blank=True)

    def amount_to_receive(self):
        if not self.amount_received_on:
            return float(self.amount) - float(self.cod_refunds.aggregate(net_amt=models.Sum('amount'))['net_amt'] or 0)

    @property
    def reference(self):
        return f"C{self.order.number}-{self.id}"


class CODRepayments(models.Model):
    cod = models.ForeignKey(COD, on_delete=models.PROTECT, related_name='cod_refunds')
    amount = models.DecimalField(max_digits=16, decimal_places=2)
    amount_received_on = models.DateTimeField(null=True, blank=True)

    @property
    def has_repaid(self):
        return self.amount_received_on is not None

    @cached_property
    def order_amount(self):
        return self.cod.order.total_incl_tax

    @property
    def amount_refunded(self):
        return self.amount is not None

    @property
    def amount_balance(self):
        return self.order_amount - self.amount_refunded

    @property
    def reference(self):
        return f"C{self.cod.order.number}-{self.cod.id}-{self.id}"

    @property
    def cod_response(self):
        return {
            'id': self.reference,
            'amount': self.amount,
            'type': 'cod',
            'collection_state': self.cod.cod_accepted,
            'collection_transfer_state': self.cod.cod_transferred,
            'transaction_date': self.amount_received_on,
        }

    def save(self, *args, **kwargs):
        if self.amount and self.amount_received_on is None:
            self.amount_received_on = timezone.now()
        super(CODRepayments, self).save(*args, **kwargs)

from django.db import models
from django.db.models import Q
from oscar.core.loading import get_model

from . import settings as app_settings


Order = get_model('order', 'Order')
OrderLine = get_model('order', 'Line')


class DeliveryTrip(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    agent = models.ForeignKey(app_settings.AGENT_MODEL, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)

    @property
    def delivery_orders(self):
        return Order.objects.filter(consignmentdelivery__delivery_trip=self)

    @property
    def delivery_returns(self):
        return Order.objects.filter(consignmentdelivery__delivery_trip=self)

    def complete_forcefully(self):
        self.delivery_consignments.update(completed=True)
        self.return_consignments.update(completed=True)
        self.completed = True
        self.save()

    def get_completed(self):
        if self.completed:
            return True
        self.completed = not any([
            self.delivery_consignments.filter(completed=False).exists(),
            self.return_consignments.filter(models.Q(completed=False)|Q(request_cancelled=True)).exists(),
        ])
        if self.completed:
            self.save()
        return self.completed

    def cods_to_collect(self):
        return

    def cods_to_return(self):
        return


class ConsignmentDelivery(models.Model):
    order = models.OneToOneField('order.Order', on_delete=models.CASCADE)
    delivery_trip = models.ForeignKey('logistics.DeliveryTrip', on_delete=models.CASCADE, null=True, blank=True,
                                      related_name='delivery_consignments')
    completed = models.BooleanField(default=False)

    def mark_as_completed(self):
        self.completed = True
        self.save()


class ConsignmentReturn(models.Model):
    order_line = models.ForeignKey('order.Line', on_delete=models.CASCADE)
    delivery_trip = models.ForeignKey('logistics.DeliveryTrip', on_delete=models.CASCADE, null=True, blank=True,
                                      related_name='return_consignments')
    request_cancelled = models.BooleanField(default=False)
    completed = models.BooleanField(default=False)

    @classmethod
    def get_instance_from_line(cls, line, as_queryset=False):
        qs = cls.objects.filter(
            request_cancelled=True, order_line=line, completed=False)
        if as_queryset:
            return qs
        return qs.last()

    @classmethod
    def cancel_consignment(cls, line):
        cls.get_instance_from_line(line, as_queryset=True).update(request_cancelled=False)

    @classmethod
    def mark_as_completed(cls, line):
        cls.get_instance_from_line(line, as_queryset=True).update(completed=True)

    @classmethod
    def generate(cls, line):
        """
        States :
            1. New Order Return Request.
            2. Re-Return Cancelled Request, which is not cancelled.
            3. Re-Return Cancelled Request, which is already cancelled. (handled as case 1)
        """
        old_pending_return_consignment = cls.get_instance_from_line(line)
        if old_pending_return_consignment:
            """ Handling Case 2 """
            old_pending_return_consignment.request_cancelled = False
            old_pending_return_consignment.save()
            return old_pending_return_consignment
        else:
            """ Handling Case 1 & 3 """
            consignment_return, is_new = cls.objects.filter(
                completed=False, request_cancelled=False).get_or_create(order_line=line)
            return consignment_return








import datetime

from django import forms
from django.db import models
from oscar.apps.dashboard.orders.forms import OrderSearchForm as OscarOrderSearchForm

from apps.order.models import TimeSlot


class OrderSearchForm(OscarOrderSearchForm):
    slot = forms.ChoiceField(
        label="Slots", required=False,
        choices=())

    def __init__(self, *args, **kwargs):
        super(OrderSearchForm, self).__init__(*args, **kwargs)
        self.fields['slot'].choices = self.slot_method_choices()

    def slot_method_choices(self):
        dt = datetime.date.today() - datetime.timedelta(days=7)
        qs = TimeSlot.objects.filter(
            start_date__gte=dt,
        ).select_related('config').order_by('-index')
        return (('', '---------'),) + tuple(
            [(slot.id, slot.slot) for slot in qs])

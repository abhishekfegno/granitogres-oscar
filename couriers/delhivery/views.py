import datetime
from django import forms
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import ListView, UpdateView, DeleteView, CreateView
from django.utils import timezone

from apps.order.models import Order
from couriers.delhivery.facade import Delhivery
from couriers.delhivery.models import RequestPickUp


class DashboardPickupListView(ListView):
    model = RequestPickUp
    ordering = ('-id', )


class DashboardPickupUpdateView(UpdateView):
    model = RequestPickUp
    fields = ('completed', )
    success_url = reverse_lazy('dashboard-pickup:list')

    def form_valid(self, form):
        form.instance.completed = True
        self.object = form.save()
        from couriers.delhivery.signals import delivery_picked_up
        print("POINT - 01")
        delivery_picked_up.send(instance=form.instance, sender=self)
        print("POINT - END")
        return HttpResponseRedirect(self.success_url)


class PickupRequestForm(forms.ModelForm):
    expected_orders = forms.IntegerField()

    def __init__(self, *args, **kwargs):
        super(PickupRequestForm, self).__init__(*args, **kwargs)
        to_pick_statuses = (settings.ORDER_STATUS_PACKED, settings.ORDER_STATUS_CONFIRMED)
        self.fields['expected_orders'].initial = Order.objects.filter(status__in=to_pick_statuses).count()

    class Meta:
        model = RequestPickUp
        fields = ('date', 'time', 'expected_orders')

    def clean_date(self):
        date = self.cleaned_data['date']
        if date < timezone.now().date():
            raise forms.ValidationError("Date needs to be a futurestic date")
        return date

    def clean_time(self):
        date = self.cleaned_data['date']
        time = self.cleaned_data['time']
        if date == timezone.now().date() and time <= timezone.now().time():
            raise forms.ValidationError("Time needs to be a futurestic time")
        if not (datetime.time(hour=9) <= time <= datetime.time(hour=21)):
            raise forms.ValidationError("Shipment can be delivered only between 09:00 AM and 09:00 PM ")
        return time


class DashboardPickupCreateView(CreateView):
    model = RequestPickUp
    form_class = PickupRequestForm
    success_url = reverse_lazy('dashboard-pickup:list')

    def form_valid(self, form):
        instance = form.instance
        d = Delhivery()
        response = d.request_pickup(instance.date, instance.time, instance)
        if response is not None and not response.get('pr_exist'):
            instance.save()
            return HttpResponseRedirect(self.success_url)
        default_message = "Invalid response form Delivery partner! please try again!"
        messages.error(self.request, (response or {}).get('error', {}).get('message', default_message))
        return self.form_invalid(form)


class DashboardPickupDeleteView(DeleteView):
    model = RequestPickUp





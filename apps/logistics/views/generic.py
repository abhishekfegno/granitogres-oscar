from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import ListView, UpdateView
from django import forms
from rest_framework import status
from rest_framework.response import Response
# from rest_framework.generics import ListAPIView

from apps.logistics.models import DeliveryTrip, ConsignmentDelivery
from apps.users.models import User


class TripCreationForm(forms.ModelForm):
    info = forms.CharField(max_length=256, required=False)
    route = forms.CharField(max_length=128, required=False, )
    agent = forms.ModelChoiceField(User.objects.filter(is_delivery_boy=True), required=True)
    selected_orders = forms.ModelMultipleChoiceField(ConsignmentDelivery.objects.all(), widget=forms.MultipleHiddenInput())
    selected_returns = forms.ModelMultipleChoiceField(ConsignmentDelivery.objects.all(), widget=forms.MultipleHiddenInput())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance is None:
            self.instance = DeliveryTrip()
        self.fields['selected_orders'].queryset = self.instance.possible_delivery_orders
        self.fields['selected_returns'].queryset = self.instance.possible_delivery_returns
        self.fields['agent'].initial = self.instance.agent_id

    class Meta:
        model = DeliveryTrip
        fields = ('agent', 'route', 'info', )


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test(lambda user:user.is_superuser), name="dispatch")
class TripUpdateView(UpdateView):
    queryset = DeliveryTrip.objects.filter(completed=False)
    template_name = 'logistics/deliverytrip_form.html'
    form_class = TripCreationForm

    def form_valid(self, form):
        self.instance = form.save()
        con_orders = self.request.POST.getlist('selected_orders')
        con_returns = self.request.POST.getlist('selected_returns')

        if self.instance.is_editable:
            possible_delivery_orders = self.object.possible_delivery_orders

            new_deliverable_consignments = possible_delivery_orders.filter(id__in=con_orders)
            deliverable_consignments_to_remove = possible_delivery_orders.exclude(id__in=con_orders)
            deliverable_consignments_to_remove.update(delivery_trip=None)       # no need to change the status.

            new_deliverable_consignments.update(delivery_trip=self.object)


            possible_return_consignments = self.object.possible_delivery_returns
            new_return_consignments = possible_return_consignments.filter(id__in=con_returns)
            return_consignments_to_remove = possible_return_consignments.exclude(id__in=con_returns)
            new_return_consignments.update(delivery_trip=self.object)
            return_consignments_to_remove.update(delivery_trip=None)

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        save_action = self.request.POST.get('save-action', '').lower()
        if 'continue' in save_action:
            return reverse('logistics:update-trip', kwargs={'pk': self.object.pk})
        if 'another' in save_action:
            return reverse('logistics:new-trip')
        return reverse('logistics:planned-trips')


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test(lambda user: user.is_superuser), name="dispatch")
class TripCreateView(TripUpdateView):

    def get_object(self, queryset=None):
        return DeliveryTrip()


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test(lambda user: user.is_superuser), name="dispatch")
class ActiveTripsListView(ListView):

    template_name = 'logistics/deliverytrip_list.html'
    queryset = DeliveryTrip.objects.filter(completed=False, is_active=True).annotate(
        order_count=Count('delivery_consignments'), refund_count=Count('return_consignments')).order_by('-id')

    def get_context_data(self, *, object_list=None, **kwargs):
        return super().get_context_data(object_list=object_list,
                                        TITLE="Active Trips",
                                        **kwargs)


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test(lambda user: user.is_superuser), name="dispatch")
class PlannedTripsListView(ListView):

    queryset = DeliveryTrip.objects.filter(completed=False, is_active=False).annotate(
        order_count=Count('delivery_consignments'), refund_count=Count('return_consignments')).order_by('-id')
    template_name = 'logistics/deliverytrip_list.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        return super().get_context_data(object_list=object_list,
                                        TITLE="Planned Trips",
                                        **kwargs)


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test(lambda user:user.is_superuser), name="dispatch")
class DeliveredTripsListView(ListView):
    queryset = DeliveryTrip.objects.filter(completed=True).annotate(
        order_count=Count('delivery_consignments'), refund_count=Count('return_consignments')).order_by('-id')
    template_name = 'logistics/deliverytrip_list.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        return super().get_context_data(object_list=object_list,
                                        TITLE="Delivered Trips",
                                        **kwargs)




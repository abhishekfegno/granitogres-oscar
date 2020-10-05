from django.conf import settings
from django.contrib import messages
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

from apps.logistics.models import DeliveryTrip, ConsignmentDelivery, ConsignmentReturn
from apps.users.models import User


class TripCreationForm(forms.ModelForm):
    info = forms.CharField(max_length=256, required=False)
    route = forms.CharField(max_length=128, required=False, )
    agent = forms.ModelChoiceField(User.objects.filter(is_delivery_boy=True), required=True)
    selected_orders = forms.ModelMultipleChoiceField(
        ConsignmentDelivery.objects.all(),      # overriding later
        required=False,
        widget=forms.MultipleHiddenInput())

    selected_returns = forms.ModelMultipleChoiceField(
        ConsignmentReturn.objects.all(),      # overriding later
        required=False,
        widget=forms.MultipleHiddenInput())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance is None:
            self.instance = DeliveryTrip()
        self.fields['selected_orders'].queryset = self.instance.possible_delivery_orders
        self.fields['selected_returns'].queryset = self.instance.possible_delivery_returns
        if self.instance:
            self.fields['agent'].initial = self.instance.agent_id

    class Meta:
        model = DeliveryTrip
        fields = ('agent', 'route', 'info', 'selected_orders', 'selected_returns', )


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test(lambda user: user.is_superuser), name="dispatch")
class TripUpdateView(UpdateView):
    queryset = DeliveryTrip.objects.order_by('-id')
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


@login_required
@user_passes_test(lambda user: user.is_superuser)
def trip_update_status_view(request, **kwargs):
    if request.method == 'POST':
        dt: DeliveryTrip = DeliveryTrip.objects.filter(pk=kwargs['pk']).last()
        action_complete_forcefully = request.POST.get('action') == 'completed_forcefully'
        action_complete = request.POST.get('action') == 'completed'
        action_start = request.POST.get('action') == 'start_trip'
        if dt is None:
            messages.error(request, "Invalid Submission")
        elif action_complete_forcefully:
            dt.complete_forcefully(reason="Order Delivery has been completed Forcefully!  ")
            messages.success(request, "Trip marked as  Completed Forcefully.")

        elif action_complete:
            try:
                dt.mark_as_completed()
            except AssertionError as e:
                messages.error(request, str(e))
                params = ''
                if settings.DEBUG:
                    params = '?complete_forcefully=1'
                return HttpResponseRedirect(
                    reverse('logistics:update-trip', kwargs={'pk': kwargs['pk']}) + params)
            else:
                messages.success(request, "Trip marked as  Completed.")
        elif action_start:
            # Validations
            if not dt.have_consignments:
                messages.error(request, "Could not start Trip, as trip neither have "
                                        "Delivery Consignments nor have Return Consignments.")

            elif not dt.agent_do_not_have_other_active_trips():
                messages.error(request, "Could not start Trip, this Agent already in  another trip.")

            elif action_start:
                dt.activate_trip()
                messages.success(request, "Trip marked as Started..")
        else:
            messages.error(request, "Invalid Action. Please select one from 'completed|start_trp'")
    else:
        messages.error(request, "Method not Allowed!")
    return HttpResponseRedirect(reverse('logistics:update-trip', kwargs={'pk': kwargs['pk']}))


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test(lambda user: user.is_superuser), name="dispatch")
class ActiveTripsListView(ListView):

    template_name = 'logistics/deliverytrip_list.html'
    queryset = DeliveryTrip.objects.filter(status=DeliveryTrip.ON_TRIP).annotate(
        order_count=Count('delivery_consignments'), refund_count=Count('return_consignments')).order_by('-id')

    def get_context_data(self, *, object_list=None, **kwargs):
        return super().get_context_data(object_list=object_list,
                                        TITLE="Active Trips",
                                        **kwargs)


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test(lambda user: user.is_superuser), name="dispatch")
class PlannedTripsListView(ListView):

    queryset = DeliveryTrip.objects.filter(status=DeliveryTrip.YET_TO_START).annotate(
        order_count=Count('delivery_consignments'), refund_count=Count('return_consignments')).order_by('-id')
    template_name = 'logistics/deliverytrip_list.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        return super().get_context_data(object_list=object_list,
                                        TITLE="Planned Trips",
                                        **kwargs)


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test(lambda user: user.is_superuser), name="dispatch")
class DeliveredTripsListView(ListView):
    queryset = DeliveryTrip.objects.filter(status=DeliveryTrip.COMPLETED).annotate(
        order_count=Count('delivery_consignments'), refund_count=Count('return_consignments')).order_by('-id')
    template_name = 'logistics/deliverytrip_list.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        return super().get_context_data(object_list=object_list,
                                        TITLE="Delivered Trips",
                                        **kwargs)


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test(lambda user: user.is_superuser), name="dispatch")
class CancalledTripsListView(ListView):
    queryset = DeliveryTrip.objects.filter(status=DeliveryTrip.CANCELLED).annotate(
        order_count=Count('delivery_consignments'), refund_count=Count('return_consignments')).order_by('-id')
    template_name = 'logistics/deliverytrip_list.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        return super().get_context_data(object_list=object_list,
                                        TITLE="Cancelled Trips",
                                        **kwargs)



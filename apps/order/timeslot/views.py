from django.urls import reverse
from django.views.generic import ListView, UpdateView, CreateView, DeleteView
from django_filters.views import FilterView

from apps.order.models import TimeSlot, TimeSlotConfiguration


class TimeSlotConfigurationListView(FilterView):
    model = TimeSlotConfiguration
    template_name = 'order/timeslot/timeslotconfiguration_list.html'
    context_object_name = 'object_list'
    filterset_fields = ('week_day_code', )


class TimeSlotConfigurationCreateView(CreateView):
    model = TimeSlotConfiguration
    template_name = 'order/timeslot/timeslotconfiguration_form.html'
    fields = '__all__'

    def get_success_url(self):
        return reverse('timeslotconfiguration-list')


class TimeSlotConfigurationUpdateView(UpdateView):
    model = TimeSlotConfiguration
    template_name = 'order/timeslot/timeslotconfiguration_form.html'
    fields = '__all__'

    def get_success_url(self):
        return reverse('timeslotconfiguration-list')


class TimeSlotConfigurationDeleteView(DeleteView):
    model = TimeSlotConfiguration
    template_name = 'order/timeslot/timeslotconfiguration_delete.html'

    def get_success_url(self):
        return reverse('timeslotconfiguration-list')


class TimeSlotListView(ListView):
    model = TimeSlot
    template_name = 'order/timeslot/timeslot_list.html'


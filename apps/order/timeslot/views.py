from django.views.generic import ListView, UpdateView, CreateView

from apps.order.models import TimeSlot, TimeSlotConfiguration


class TimeSlotConfigurationListView(ListView):
    model = TimeSlotConfiguration
    template_name = 'order/timeslot/timeslotconfiguration_list.html'


class TimeSlotConfigurationCreateView(CreateView):
    model = TimeSlotConfiguration
    template_name = 'order/timeslot/timeslotconfiguration_form.html'
    fields = '__all__'


class TimeSlotConfigurationUpdateView(UpdateView):
    model = TimeSlotConfiguration
    template_name = 'order/timeslot/timeslotconfiguration_form.html'
    fields = '__all__'


class TimeSlotListView(ListView):
    model = TimeSlot
    template_name = 'order/timeslot/timeslot_list.html'


from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, UpdateView, ListView, DeleteView

from .forms import ZoneForm
from ..models import Zones


class ZoneSelector(ListView):
    model = Zones
    fields = ('zone', 'name')
    template_name = 'availability/zones/list.html'


class ZoneUpdate(UpdateView):
    form_class = ZoneForm
    queryset = Zones.objects.all()
    template_name = 'availability/zones/form.html'


class ZoneCreate(CreateView):
    form_class = ZoneForm
    queryset = Zones.objects.all()
    template_name = 'availability/zones/form.html'

    def get_success_url(self):
        return reverse('availability:zone-update',  kwargs={'pk': self.object})


class ZoneDelete(DeleteView):
    model = Zones
    fields = ('zone', 'name')
    template_name = 'availability/zones/delete.html'
    success_url = reverse_lazy('availability:zones-list')

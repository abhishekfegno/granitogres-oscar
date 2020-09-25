from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, UpdateView, ListView, DeleteView
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .facade import ZoneFacade
from .forms import ZoneForm
from .serializers import DeliverabilityCheckSerializer
from ..models import Zones
from .. import settings as app_settings


class ZoneSelector(ListView):
    model = Zones
    fields = ('zone', 'name')
    template_name = 'availability/zones/list.html'


class ZoneUpdate(UpdateView):
    form_class = ZoneForm
    queryset = Zones.objects.all()
    template_name = 'availability/zones/form.html'

    def get_success_url(self):
        return reverse('availability:zones-update',  kwargs={'pk': self.object.pk})

class ZoneCreate(CreateView):
    form_class = ZoneForm
    queryset = Zones.objects.all()
    template_name = 'availability/zones/form.html'

    def get_success_url(self):
        return reverse('availability:zones-update',  kwargs={'pk': self.object.pk})


class ZoneDelete(DeleteView):
    model = Zones
    fields = ('zone', 'name')
    template_name = 'availability/zones/delete.html'
    success_url = reverse_lazy('availability:zones-list')


class SetZone(GenericAPIView):
    """
    Method : POST
    Login Required : optional;


    ## A Working location.
    'SRID=4326;POINT (77.94478155806023 12.785238498732)'

    {
        "latitude": "12.785238498732",
        "longitude": "77.94478155806023"
    }

    """
    serializer_class = DeliverabilityCheckSerializer
    permission_classes = [AllowAny, ]

    def get(self, request, *args, **kwargs):
        return Response(ZoneFacade().face(request))

    def post(self, request, *args, **kwargs):
        sobj = self.get_serializer(data=request.data)
        if not sobj.is_valid():
            return Response(sobj.errors, status=status.HTTP_400_BAD_REQUEST)
        point = sobj.validated_data['point']
        zone = sobj.validated_data['zone']
        _out = ZoneFacade().set_zone(request, zone=zone, point=point)
        return Response(_out)


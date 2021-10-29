from django.conf import settings
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, UpdateView, ListView, DeleteView
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .forms import ZoneForm
from .serializers import DeliverabilityCheckSerializer
from ..base.facade import BaseZoneFacade
from ..facade import ZoneFacade
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
        "longitude": "77.94478155806023".
        "pincode": null
    }
    """
    http_method_names = ['get', 'post']
    permission_classes = [AllowAny, ]
    serializer_class = DeliverabilityCheckSerializer

    def get(self, request, *args, **kwargs):
        return Response(ZoneFacade.face(request))

    def post(self, request, *args, **kwargs):
        # import pdb;pdb.set_trace()
        sobj = self.get_serializer(data=request.data)
        if not sobj.is_valid():
            out = {'error_message': "Sorry, We are unable to deliver to this location now!"}
            return Response(out, status=status.HTTP_400_BAD_REQUEST)
        _out = sobj.validated_data['facade_object'].set_zone(request)
        return Response(_out)


class UnsetZone(GenericAPIView):
    permission_classes = [AllowAny, ]

    def get(self, request, *args, **kwargs):
        for key in ['zone', 'zone_name', 'location', 'location_name', 'pincode']:
            if key in request.session:
                del request.session[key]

        location = BaseZoneFacade.get_location_util(request)
        if location:
            for MODE in settings.LOCATION_FETCHING_MODE_SET:
                attr_name = f'get_{MODE}_data'
                if hasattr(location, attr_name) and callable(getattr(location, attr_name)):
                    keys = getattr(location, attr_name)().keys()
                    for key in keys:
                        if key in request.session:
                            del request.session[key]

        return Response(ZoneFacade.face(request))


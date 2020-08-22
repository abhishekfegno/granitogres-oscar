from typing import Any

from rest_framework import status, authentication
from rest_framework.generics import ListAPIView, RetrieveAPIView, UpdateAPIView, GenericAPIView
from rest_framework.mixins import RetrieveModelMixin
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.logistics.models import DeliveryTrip
from apps.logistics.serializers import DeliveryTripSerializer


class OrdersListView(APIView):
    http_method_names = ['get', ]
    authentication_classes = (authentication.SessionAuthentication, )

    def get(self, request, *args, **kwargs):
        return Response({}, status=status.HTTP_204_NO_CONTENT)


class OrdersDetailView(APIView):
    http_method_names = ['post', ]
    authentication_classes = (authentication.SessionAuthentication, )

    def post(self, request, *args, **kwargs):
        return Response({}, status=status.HTTP_204_NO_CONTENT)


class DeliveredTripsListView(ListAPIView):
    serializer_class = DeliveryTripSerializer
    authentication_classes = (authentication.SessionAuthentication, )

    def get_queryset(self):
        return DeliveryTrip.objects.filter(agent=self.request.user)


class DeliveredTripsDetailView(RetrieveAPIView):
    serializer_class = DeliveryTripSerializer
    authentication_classes = (authentication.SessionAuthentication, )

    def get_queryset(self):
        return DeliveryTrip.objects.filter(agent=self.request.user)


class ActiveTripView(GenericAPIView):
    """
    Get : Get active Trip
    POST :
        Body : {
            "action": "completed"       <-- when you finally complete the trip.
        }

    Return status :
        204 : when there is not active trip found.
        200 : On any successful response.
        400 : Invalid Action.
    """
    serializer_class = DeliveryTripSerializer
    authentication_classes = (authentication.SessionAuthentication, )

    def post(self, request, *args, **kwargs):
        instance: Any(DeliveryTrip, None) = self.get_object()
        if instance is None:
            return Response({"details": "No active Trips Found"}, status=status.HTTP_204_NO_CONTENT)
        if request.POST.get('action') == 'completed':
            instance.complete_forcefully()
            return Response({
                "details": "Trip Completed.",
            })
        return Response({"details": "Invalid Action"}, status=status.HTTP_400_BAD_REQUEST)

    def get_object(self):
        return DeliveryTrip.get_active_trip(agent=self.request.user, raise_error=False)

    def get(self, request, *args, **kwargs):
        instance: Any(DeliveryTrip, None) = self.get_object()
        if instance:
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        return Response({"details": "No active Trips Found"}, status=status.HTTP_204_NO_CONTENT)

    def get_queryset(self):
        return DeliveryTrip.objects.filter(agent=self.request.user)


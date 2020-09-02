from typing import Any

from django.utils.decorators import method_decorator
from oscarapi.serializers.checkout import OrderLineSerializer
from rest_framework import status, authentication
from rest_framework.authentication import SessionAuthentication, BaseAuthentication
from rest_framework.decorators import api_view
from rest_framework.generics import ListAPIView, RetrieveAPIView, UpdateAPIView, GenericAPIView, get_object_or_404
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api_set.serializers.orders import OrderListSerializer, OrderDetailSerializer, OrderMoreDetailSerializer, \
    LineDetailSerializer
from apps.logistics.models import DeliveryTrip, ConsignmentReturn
from apps.logistics.serializers import DeliveryTripSerializer
from apps.order.models import Order


def _delivery_boy_login_required(func):
    def _wrapper(request, *args, **kwargs):
        if request.user.is_anonymous:
            return Response({'detail': 'Authentication Required'}, status=status.HTTP_400_BAD_REQUEST)
        if not request.user.is_delivery_boy or request.user.is_delivery_request_pending:
            return Response({'detail': 'You are currently banned to access this application.'},
                            status=status.HTTP_400_BAD_REQUEST)
        return func(request, *args, **kwargs)
    _wrapper.__doc__ = func.__doc__
    obj = func if hasattr(func, '__name__') else func.__class__
    _wrapper.__name__ = obj.__name__
    return _wrapper


class DeliveryBoyPermission(BasePermission):

    def has_permission(self, request, view):
        user = getattr(request._request, 'user', None)
        return user and user.is_active and user.is_delivery_boy and not user.is_delivery_request_pending

    def has_object_permission(self, request, view, obj):
        return obj.agent == request.user


@method_decorator(_delivery_boy_login_required, 'dispatch')
class OrdersListView(APIView):
    http_method_names = ['get', ]
    authentication_classes = (SessionAuthentication, )
    permission_classes = [DeliveryBoyPermission, ]

    def get(self, request, *args, **kwargs):
        return Response({}, status=status.HTTP_204_NO_CONTENT)


class DeliveredTripsListView(ListAPIView):
    serializer_class = DeliveryTripSerializer
    authentication_classes = (SessionAuthentication, )
    permission_classes = [DeliveryBoyPermission, ]

    def get_queryset(self):
        return DeliveryTrip.objects.filter(agent=self.request.user, status=DeliveryTrip.COMPLETED)


class CancelledTripsListView(ListAPIView):
    serializer_class = DeliveryTripSerializer
    authentication_classes = (SessionAuthentication, )
    permission_classes = [DeliveryBoyPermission, ]

    def get_queryset(self):
        return DeliveryTrip.objects.filter(agent=self.request.user, status=DeliveryTrip.CANCELLED)


class PlannedTripView(ListAPIView):
    serializer_class = DeliveryTripSerializer
    authentication_classes = (SessionAuthentication, )
    permission_classes = [DeliveryBoyPermission, ]

    def get_queryset(self):
        return DeliveryTrip.objects.filter(agent=self.request.user, status=DeliveryTrip.YET_TO_START)



class TripsDetailView(RetrieveAPIView):
    serializer_class = DeliveryTripSerializer
    authentication_classes = (SessionAuthentication, )
    permission_classes = [DeliveryBoyPermission, ]

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
    authentication_classes = (SessionAuthentication, )
    permission_classes = [DeliveryBoyPermission, ]

    def post(self, request, *args, **kwargs):
        instance: Any(DeliveryTrip, None) = self.get_object()
        if instance is None:
            return Response({"details": "No active Trips Found"}, status=status.HTTP_204_NO_CONTENT)
        if request.POST.get('action') == 'completed':
            have_delivery_consignments = instance.delivery_consignments.filter(completed=False).exists()
            have_delivery_consignments = instance.delivery_consignments.filter(completed=False).exists()
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


@api_view(("GET",))
@_delivery_boy_login_required
def orders_detail(request, *a, **k):
    dt = DeliveryTrip.get_active_trip(agent=request.user, raise_error=False) or DeliveryTrip()
    _object = get_object_or_404(dt.delivery_orders, pk=k.get('pk'))
    serializer_class = OrderDetailSerializer
    return Response(serializer_class(_object, context={'request': request}).data)


@api_view(("GET",))
@_delivery_boy_login_required
def orders_more_detail(request, *a, **k):
    dt = DeliveryTrip.get_active_trip(agent=request.user, raise_error=False) or DeliveryTrip()
    _object = get_object_or_404(dt.delivery_orders, pk=k.get('pk'))
    serializer_class = OrderMoreDetailSerializer
    return Response(serializer_class(_object, context={'request': request}).data)


@api_view(("GET",))
@_delivery_boy_login_required
def orders_item_detail(request, *a, **k):
    dt = DeliveryTrip.get_active_trip(agent=request.user, raise_error=False) or DeliveryTrip()
    _object = get_object_or_404(dt.delivery_returns, pk=k.get('pk'))
    serializer_class = LineDetailSerializer
    return Response(serializer_class(_object, context={'request': request}).data)


@api_view(("POST",))
@_delivery_boy_login_required
def order_delivered_status_change(request, method, pk, action, *a, **k):
    """
    method: {order|return}
    pk: <consignment_id>
    action {complete|cancel} """
    dt = DeliveryTrip.get_active_trip(agent=request.user, raise_error=False) or DeliveryTrip()
    out = {}
    status_code = 200
    if method == 'order':
        consignment_object = get_object_or_404(dt.delivery_consignments, pk=k.get('pk'))
        if action == 'complete':
            consignment_object.mark_as_completed()
        elif action == "cancel":
            consignment_object.cancel_consignment()
        else:
            out = {'error': 'Invalid Action. Action can either be "completed" or "cancelled"'}
            status_code = 400
    elif method == 'return':
        consignment_object = get_object_or_404(dt.return_consignments, pk=k.get('pk'))
        if action == 'complete':
            consignment_object.mark_as_completed()
        elif action == "cancel":
            consignment_object.cancel_consignment()
        else:
            out = {'error': 'Invalid Action. Action can either be "completed" or "cancelled"'}
            status_code = 400
    else:
        out = {'error': 'Invalid Type'}
        status_code = 400

    return Response(out, status=status_code)



from datetime import datetime
from typing import Any

from django.utils.decorators import method_decorator
from oscar_accounts.models import Transfer, Transaction
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view
from rest_framework.generics import ListAPIView, RetrieveAPIView, GenericAPIView, get_object_or_404, \
    RetrieveUpdateAPIView
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api_set.serializers.orders import OrderListSerializer, OrderDetailSerializer, OrderMoreDetailSerializer, \
    LineDetailSerializer
from apps.logistics.models import DeliveryTrip
from apps.logistics.serializers import DeliveryTripSerializer, ArchivedTripListSerializer, TransactionSerializer
from apps.logistics.utils import TransferCOD
from apps.order.models import Sum


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


class ArchivedTripsListView(ListAPIView):
    serializer_class = ArchivedTripListSerializer
    authentication_classes = (SessionAuthentication, )
    permission_classes = [DeliveryBoyPermission, ]

    def get_queryset(self):
        trip_date = None
        try:
            trip_date = datetime.strptime(self.kwargs['trip_date'], "%d-%m-%Y")
        except ValueError as e:
            return Response({"detail": "Date is not valid"}, status=status.HTTP_404_NOT_FOUND)
        return DeliveryTrip.objects.filter(
            agent=self.request.user,
            status__in=(DeliveryTrip.COMPLETED, DeliveryTrip.CANCELLED),
            trip_date=trip_date,
        )


class TripsDetailView(RetrieveUpdateAPIView):
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
    dt = DeliveryTrip.get_active_trip(agent=request.user, raise_error=False)
    if dt is None:
        return Response({'error': ''}, status=400)
    out = {}

    def catch_error(func, args=(), kwargs=None):
        if kwargs is None:
            kwargs = {}
        try:
            return func(*args, **kwargs), None
        except Exception as e:
            return None, {'error': str(e)}

    status_code = 200
    reason = request.GET.get('reason')
    if method == 'order':
        consignment_object = get_object_or_404(dt.delivery_consignments, pk=pk)
        if action == 'complete':
            _, err = catch_error(consignment_object.mark_as_completed, args=(reason, ))
            out = err
        elif action == "cancel":
            _, err = catch_error(consignment_object.cancel_consignment, args=(reason, ))
            out = err
        else:
            out = {'error': 'Invalid Action. Action can either be "completed" or "cancelled"'}
            status_code = 400
    elif method == 'return':
        consignment_object = get_object_or_404(dt.return_consignments, pk=pk)
        if action == 'complete':
            _, err = catch_error(consignment_object.mark_as_completed, args=(reason, ))
            out = err
        elif action == "cancel":
            _, err = catch_error(consignment_object.cancel_consignment, args=(reason, ))
            out = err
        else:
            out = {'error': 'Invalid Action. Action can either be "completed" or "cancelled"'}
            status_code = 400
    elif method == 'trip':
        consignment_object = dt
        if action == 'complete':
            _, err = catch_error(consignment_object.mark_as_completed, args=(reason, ))
            out = err
        elif action == "cancel":
            _, err = catch_error(consignment_object.cancel_consignment, args=(reason, ))
            out = err
        else:
            out = {'error': 'Invalid Action. Action can either be "completed" or "cancelled"'}
            status_code = 400
    else:
        out = {'error': 'Invalid Type. Type can be "order" or "return"'}
        status_code = 400

    if out and out.keys():
        status_code = 400
    else:
        action += ('d' if action == 'completed' else 'led')
        out = {"message": f"Successful! {method} #{pk} {action}"}
    return Response(out, status=status_code)


@method_decorator(_delivery_boy_login_required, name="dispatch")
class TransactionList(ListAPIView):
    model = Transfer
    serializer_class = TransactionSerializer

    def get_queryset(self):
        return TransferCOD(self.request.user).get_my_transactions().select_related(
            'source', 'source__account_type', 'destination', 'destination__account_type').order_by('-date_created')


@api_view()
@_delivery_boy_login_required
def archived_transaction_list_summery(request, trip_date):
    try:
        trip_date = datetime.strptime(trip_date, "%d-%m-%Y")
    except ValueError as e:
        return Response({"detail": "Date is not valid"}, status=status.HTTP_404_NOT_FOUND)
    transfers = Transaction.objects.filter(
        date_created__date=trip_date, account__primary_user=request.user
    )
    credit_transfers = transfers.filter(amount__gt=0).aggregate(sum=Sum('amount'))['sum'] or 0
    debit_transfers = transfers.filter(amount__lt=0).aggregate(sum=Sum('amount'))['sum'] or 0
    return Response({
        'credit_transfers': credit_transfers,
        'debit_transfers': debit_transfers,
        'balance_transfers': credit_transfers + debit_transfers
    })


class ArchivedTransactionList(TransactionList):

    def get_queryset(self):
        try:
            trip_date = datetime.strptime(self.kwargs['trip_date'], "%d-%m-%Y")
        except ValueError as e:
            return Response({"detail": "Date is not valid"}, status=status.HTTP_404_NOT_FOUND)
        return TransferCOD(self.request.user).get_my_transactions(
        ).filter(date_created__date=trip_date).select_related(
            'source', 'source__account_type', 'destination', 'destination__account_type').order_by('-date_created')


class PlannedTripListView(ListAPIView):
    model = DeliveryTrip
    serializer_class = ArchivedTripListSerializer
    
    def get_queryset(self):
        return super(PlannedTripListView, self).get_queryset().filter(agent=self.request.user, status=self.model.YET_TO_START)




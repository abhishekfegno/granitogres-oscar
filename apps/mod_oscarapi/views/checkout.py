import pprint
from collections import Iterable

from django.db.models import F
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.conf import settings
from oscarapi.permissions import IsOwner
from rest_framework.permissions import IsAuthenticated

from apps.address.models import UserAddress
from oscar.core import prices
from oscarapi.basket.operations import assign_basket_strategy
from oscarapicheckout import utils
from oscarapicheckout.serializers import OrderSerializer
from oscarapicheckout.signals import order_placed
from oscarapicheckout.states import DECLINED, CONSUMED
from oscarapicheckout.utils import CHECKOUT_ORDER_ID
from oscarapicheckout.views import CheckoutView as OscarAPICheckoutView
from rest_framework import status, serializers, generics
from rest_framework.response import Response
from rest_framework.reverse import reverse

from ..calculators import OrderTotalCalculator
from ..serializers.checkout import (
    CheckoutSerializer, UserAddressSerializer,
)
from ...api_set.views.orders import _login_required
from ...basket.models import Basket
from ...checkout.collector import Casher
from ...checkout.payment_view_mixins.cod_view import CodPaymentMixin
from ...checkout.payment_view_mixins.razor_pay_view import RazorPayPaymentMixin
from ...order.models import TimeSlot
from ...payment import refunds
from ...shipping.repository import Repository
from ...api_set.serializers.basket import WncBasketSerializer
from ...basket.utils import order_to_basket


def _login_and_location_required(func):
    def _wrapper(request, *args, **kwargs):
        if request.user.is_anonymous:
            return JsonResponse({'detail': 'You have to be logged-in to create Order.'},
                                status=status.HTTP_400_BAD_REQUEST)
        if not request.session.get('location'):
            return JsonResponse({'detail': 'Geolocation not provided'}, status=status.HTTP_400_BAD_REQUEST)
        return func(request, *args, **kwargs)

    return _wrapper


@method_decorator(_login_required, name="dispatch")
class CheckoutView(CodPaymentMixin, RazorPayPaymentMixin, OscarAPICheckoutView):
    __doc__ = """
    Prepare an order for checkout.

    NEW FROMAT:
    POST 
    # COD
    {
        "basket": f"https://store.demo.fegno.com/api/v1/baskets/{basket.id}/",
        "basket_id": basket.id,
        # "total": float(basket.total_incl_tax),
        "notes": "Some Notes for address as string.",
        "phone_number": "+919497270863",
        "shippingcode": <"self-shipping"|"express-delivery">,
        "shipping_address": (User Address ID),
        "billing_address": (User Address ID),
        "payment": cash,
        "slot": slot.id,
    }
    # Prepaid
    {
        "basket": f"https://store.demo.fegno.com/api/v1/baskets/{basket.id}/",
        "basket_id": basket.id,
        # "total": float(basket.total_incl_tax),
        "notes": "Some Notes for address as string.",
        "phone_number": "+919497270863",
        "shippingcode": <"self-shipping"|"express-delivery">,
        "shipping_address": (User Address ID),
        "billing_address": (User Address ID),
        "payment": "razor_pay",
        "razorpay_payment_id": "pay_A2IJ20983u498hR"
        "slot": slot.id,
    }

    OLD DEPRICATED FORMAT
    POST(basket, shipping_address,
    [total, shipping_method_code, shipping_charge, billing_address]):
    {
        "basket":"https://store.demo.fegno.com/api/v1/baskets/8853/",
        "guest_email":"",
        "total":5413.13,
        "shipping_method_code":"free_shipping",
        "shipping_charge":{
            "excl_tax": 0.0,
            "currency": "INR",
            "incl_tax": 0.0,
            "tax": 0.0
        },
        "shipping_address":{
            "title":"Mr",
            "first_name":"JERIN",
            "last_name":"JOHN",
            "line1":"Kachirackal House",
            "line2":"Vennikulam P O",
            "line3":"Thiruvalla",
            "line4":"Thiruvalla",
            "state":"Kerala",
            "postcode":"689544",
            "phone_number":"+919446600863",
            "notes":"",
            "country":"https://store.demo.fegno.com/api/v1/countries/IN/"
        },
        "billing_address":{
            "title":"Mr",
            "first_name":"JERIN",
            "last_name":"JOHN",
            "line1":"Kachirackal House",
            "line2":"Vennikulam P O",
            "line3":"Thiruvalla",
            "line4":"Thiruvalla",
            "state":"Kerala",
            "postcode":"689544",
            "phone_number":"+919446600863",
            "notes":"",
            "country":"https://store.demo.fegno.com/api/v1/countries/IN/"
        },
        "payment":{
            "cash": {
            "enabled": true,
            "pay_balance": true
            }
        }
    }

    OR ANOTHER PAYMENT OBJECT (Pay 10000.0 With razorpay and pay balance with cash.)
    "payment":{
        "cash":{
            "enabled": true,
            "pay_balance": true,
        },
        "razor_pay": {
            "enabled": true,
            "amount": "10000.00",
            "razorpay_payment_id": "pay_zk324df2...."
        }
    }
    YET OR ANOTHER PAYMENT OBJECT (PAY COD.)
    "payment":{
        "cash":{
            "enabled": true,
            "pay_balance": true,
        },
        "razor_pay": {
            "enabled": false,
        }
    }

    API Supports multiple payments integration, though our system doesnot' well support this feature. (futurestic one.)
    returns the order object.

    """
    serializer_class = CheckoutSerializer
    order_object = None

    def post_format(self, request, format=None):
        # Wipe out any previous state data
        utils.clear_consumed_payment_method_states(request)
        user = request.user if request.user and request.user.is_authenticated else None
        # Validate the input
        data = request.data.copy()
        basket = Basket.objects.filter(pk=data.get('basket_id', 0)).filter(owner=user).first()

        if basket is None:
            return Response({'errors': "Basket does not Exists"}, status=status.HTTP_406_NOT_ACCEPTABLE)
        basket = assign_basket_strategy(basket, request)
        if basket.is_empty:
            return Response({'errors': "Basket is Empty!"}, status=status.HTTP_406_NOT_ACCEPTABLE)

        shipping_address = UserAddress.objects.filter(user=user, pk=data.get('shipping_address')).first()
        if shipping_address is None:
            return Response({'errors': "User Address for shipping does not exists"},
                            status=status.HTTP_406_NOT_ACCEPTABLE)

        billing_address = UserAddress.objects.filter(user=user, pk=data.get('billing_address')).first()
        if billing_address is None:
            return Response({'errors': "User Address for billing does not exists"},
                            status=status.HTTP_406_NOT_ACCEPTABLE)

        try:
            ship = None
            shippingcode = data.get('shippingcode', 'self-shipping')
            for repo in Repository().get_available_shipping_methods(basket, user=user, shipping_addr=shipping_address,
                                                                    request=request, ):
                if repo.code == shippingcode:
                    ship = repo
                break
            if ship is None:
                methods_are = ", ".join([r.code for r in Repository().get_available_shipping_methods(basket)])
                return Response(
                    {'errors': f"Please Choose a valid Shipping Method! (Allowed methods are: {methods_are})"},
                    status=status.HTTP_406_NOT_ACCEPTABLE)
        except serializers.ValidationError:
            return Response({'errors': "User Address for billing does not exists"},
                            status=status.HTTP_406_NOT_ACCEPTABLE)
        basket_errors = []
        for line in basket.all_lines():
            result = basket.strategy.fetch_for_line(line)
            is_permitted, reason = result.availability.is_purchase_permitted(line.quantity)
            if not is_permitted:
                # Create a meaningful message to return in the error response
                # Translators: User facing error message in checkout
                msg = "This item is no longer available to buy." % {
                    'title': line.product.get_title(),
                    'reason': reason,
                }
                basket_errors.append(msg)
            elif not is_permitted:
                # Create a meaningful message to return in the error response
                # Translators: User facing error message in checkout
                msg = "This item is no longer available to buy." % {
                    'title': line.product.get_title(),
                    'reason': reason,
                }
                basket_errors.append(msg)
        if basket_errors:
            return Response({'errors': "\n".join(basket_errors)}, status=status.HTTP_406_NOT_ACCEPTABLE)

        shipping_cost: prices.Price = ship.calculate(basket)
        # total_amt = float(basket.total_incl_tax + shipping_cost.incl_tax)
        total_amt = OrderTotalCalculator(request=request).calculate(basket, shipping_cost)
        sample_data = {
            "basket": request.build_absolute_uri(reverse("basket-detail", kwargs={'pk': basket.pk})),
            # "total": total_amt.incl_tax,
            "shipping_method_code": ship.code,
            "shipping_charge": {
                "excl_tax": shipping_cost.excl_tax,
                "currency": shipping_cost.currency,
                "incl_tax": shipping_cost.incl_tax,
                "tax": 0.0
            },
            "shipping_address": {
                "title": shipping_address.title,
                "first_name": shipping_address.first_name,
                "last_name": shipping_address.last_name,
                "line1": shipping_address.line1,
                "line2": shipping_address.line2,
                "line3": shipping_address.line3,
                "line4": shipping_address.line4,
                "state": shipping_address.state,
                "postcode": shipping_address.postcode,
                "address_type": shipping_address.address_type,
                "phone_number": data.get('phone_number') or f"+91 {request.user.username}",
                "notes": data.get('notes'),
                "country": request.build_absolute_uri(f"/api/v1/countries/{shipping_address.country.pk}/"),
                "location": f'POINT({shipping_address.location.x} {shipping_address.location.y})' if shipping_address.location else None
            },
            "billing_address": {
                "title": shipping_address.title,
                "first_name": shipping_address.first_name,
                "last_name": shipping_address.last_name,
                "line1": shipping_address.line1,
                "line2": shipping_address.line2,
                "line3": shipping_address.line3,
                "line4": shipping_address.line4,
                "state": shipping_address.state,
                "postcode": shipping_address.postcode,
                "phone_number": data.get('phone_number') or f"+91 {request.user.username}",
                "notes": data.get('notes'),
                "country": request.build_absolute_uri(f"/api/v1/countries/{shipping_address.country.pk}/")
            },
            "payment": {
                "cash": {
                    "enabled": data.get('payment') == 'cash',
                    "amount": total_amt.incl_tax if data.get('payment') == 'cash' else 0,
                },
                "razor_pay": {
                    "enabled": data.get('payment') == 'razor_pay',
                    "amount": total_amt.incl_tax if data.get('payment') == 'razor_pay' else 0,
                    "razorpay_payment_id": data.get('razorpay_payment_id')
                }
            }
        }
        c_ser = self.get_serializer(data=sample_data)
        if not c_ser.is_valid():
            string = ""
            for key, data in c_ser.errors.items():
                key_str = key
                _error = str(data)
                if type(data) is dict:
                    for new_key, error_text in data.items():
                        key_str += '.' + new_key
                        _error = str(error_text[0]) if error_text and isinstance(error_text, Iterable) else str(
                            error_text)
                string += f"{key_str}:{_error}\n"

            return Response(c_ser.errors, status.HTTP_406_NOT_ACCEPTABLE)
        # location = shipping_address.location
        # if not location:
        #     return Response({'errors': "You have not provided your location yet."},
        #                     status=status.HTTP_406_NOT_ACCEPTABLE)
        # Freeze basket
        basket = c_ser.validated_data.get('basket')
        basket.freeze()

        # Save Order
        order = c_ser.save()
        slot_changed = None
        if settings.TIME_SLOT_ENABLED:
            slots = TimeSlot.get_upcoming_slots()
            if data.get('slot'):
                for slot in slots:
                    if slot.id == data.get('slot'):
                        order.slot = slot
                        order.save()
            if order.slot is None and slots:
                order.slot = slots[0]
                order.save()
            slot_changed = data.get('slot') == order.slot_id
        self.order_object = order
        request.session[CHECKOUT_ORDER_ID] = order.id

        # adding location from user request to
        # order.shipping_address.location = location
        # order.shipping_address.save()
        # Send order_placed signal
        order_placed.send(sender=self, order=order, user=request.user, request=request)

        # Save payment steps into session for processing
        # previous_states = utils.list_payment_method_states(request)
        # new_states = self._record_payments(
        #     previous_states=previous_states,
        #     request=request,
        #     order=order,
        #     methods=c_ser.fields['payment'].methods,
        #     data=c_ser.validated_data['payment'])
        # utils.set_payment_method_states(order, request, new_states)

        o_ser = OrderSerializer(order, context={'request': request})

        # if order.status == settings.ORDER_STATUS_PAYMENT_DECLINED:
        #     basket = order_to_basket(order, request=request)
        #     b_ser = WncBasketSerializer(basket, context={'request': request})
        #     return Response({
        #         'errors': "Payment Declined!",
        #         'new_basket': b_ser.data,
        #         'failed_order': o_ser.data,
        #     }, status=status.HTTP_406_NOT_ACCEPTABLE)

        ord_sers = []  # must be sent as checkout response
        ord_statuses = []
        # Return order data
        data = o_ser.data
        data['errors'] = None
        data['slot_changed'] = slot_changed
        slot = order.slot
        data['slot'] = {
            'pk': slot and slot.pk,
            'start_time': slot and slot.config.start_time,
            'end_time': slot and slot.config.end_time,
            'start_date': slot and slot.start_date,
            'max_datetime_to_order': slot and slot.max_datetime_to_order,
            'is_next': bool(slot),
            'index': slot and slot.index,
        }
        ord_sers.append(data)
        ord_statuses.append(order.status)

        _status = settings.ORDER_STATUS_PLACED
        # self.handle_payment_for_orders(orders, order_total=total_amt.incl_tax, payment_data=sample_data['payment'])

        try:
            self.handle_payment_for_orders(order, order_total=total_amt.incl_tax, payment_data=sample_data['payment'])
        except Exception as e:
            print("handle_payment_for_orders >> ", e)

            order.set_status(settings.ORDER_STATUS_PAYMENT_DECLINED)
            # return Response({"errors": "Payment Declined"})
            return Response({"errors": str(e)}, status=status.HTTP_406_NOT_ACCEPTABLE)

        print("------------------ 10 ")
        b_ser = WncBasketSerializer(basket, context={'request': request})

        if settings.ORDER_STATUS_PAYMENT_DECLINED in ord_statuses:
            basket.thaw()
            return Response({
                'errors': _status,
                'new_basket': b_ser.data,
                'orders': ord_sers,
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        return Response({
            'status': _status,
            'new_basket': b_ser.data,
            'orders': ord_sers,
        }, status=status.HTTP_201_CREATED)

        # return Response(data)
    def handle_payment_for_orders(self, order, order_total, payment_data):
        order_total = float(order_total)
        casher = Casher(payment_data)
        casher.collect(order_total, order)

    def post(self, request, format=None):
        try:
            resp = self.post_format(request, format=None)
            if resp.status_code == status.HTTP_406_NOT_ACCEPTABLE:
                payment_refunded = False
                try:
                    if self.order_object:
                        refunds.RefundFacade().refund_order(order=self.order_object)
                        self.order_object.lines.update(refunded_quantity=F('quantity'))
                except:
                    pass
            return resp
        except Exception as e:
            print(e)
            return Response({'errors': str(e)}, status=status.HTTP_406_NOT_ACCEPTABLE)

    def _record_payments(self, previous_states, request, order, methods, data):
        order_balance = [order.total_incl_tax]
        new_states = {}

        def record(method_key, method_data):
            # If a previous payment method at least partially succeeded, hasn't been consumed by an
            # order, andx` is for the same amount, recycle it. This requires that the amount hasn't changed.

            # Get the processor class for this method
            code = method_data['method_type']
            method = methods[code]

            state = None
            if method_key in previous_states:
                prev = previous_states[method_key]
                if prev.status not in (DECLINED, CONSUMED):
                    if prev.amount == method_data['amount']:
                        state = prev
                    else:
                        # Previous payment exists but we can't recycle it; void whatever already exists.
                        method.void_existing_payment(request, order, method_key, prev)

            # Previous payment method doesn't exist or can't be reused. Create it now.
            if not state:
                method_data.update()
                state = method.record_payment(request, order, method_key, **method_data)
            # Subtract amount from pending order balance.
            order_balance[0] = order_balance[0] - state.amount
            return state

        # Loop through each method with a specified amount to charge
        data_amount_specified = {k: v for k, v in data.items() if not v['pay_balance'] and v['enabled']}
        for key, method_data in data_amount_specified.items():
            new_states[key] = record(key, method_data)

        # Change the remainder, not covered by the above methods, to the method marked with `pay_balance`
        data_pay_balance = {k: v for k, v in data.items() if v['pay_balance'] and v['enabled']}
        for key, method_data in data_pay_balance.items():
            method_data['amount'] = order_balance[0]
            new_states[key] = record(key, method_data)

        return new_states


class UserAddressList(generics.ListCreateAPIView):
    serializer_class = UserAddressSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return UserAddress.objects.filter(user=self.request.user)


class UserAddressDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserAddressSerializer
    permission_classes = (IsOwner,)

    def get_queryset(self):
        return UserAddress.objects.filter(user=self.request.user)



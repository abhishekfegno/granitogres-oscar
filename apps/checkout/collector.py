import math
from django.conf import settings
from apps.payment.models import SourceType
from apps.payment.models import Source


from apps.checkout import PAYMENT_METHOD_STRIPE, PAYMENT_METHOD_CASH, PAYMENT_EVENT_PURCHASE, PAYMENT_METHOD_RAZORPAY, \
    RAZOR_PAY_TOKEN
from apps.order.models import PaymentEventType, PaymentEvent

from apps.checkout.facade.razorpay import RazorPayFacade
from apps.payment.models import COD, PaymentGateWayResponse


class BasePaymentMethod:
    token = None

    def collect(self, net_amount, payment_data):
        raise NotImplementedError()

    def record_payment(self, order, net_amount, reference="", **kwargs):
        raise NotImplementedError()

    def payment_description(self, order_group_number, order_number, net_amt, order_total, **kwargs):
        from datetime import datetime
        from pytz import timezone
        ist = timezone('Asia/Kolkata')
        ist_time = datetime.now(ist)
        return f"Net payment of {net_amt}  with {settings.SITE_NAME} against order group #{order_group_number} and " \
               f"#{order_number} INR with an amount of " \
               f" {order_total} INR on {ist_time.strftime('%Y-%m-%d_%H-%M-%S')}"

    def payment_metadata(self, **kwargs):
        return kwargs

    def add_payment_event(self, event_type_name, amount, reference=''):
        """
        Record a payment event for creation once the order is placed
        """
        event_type, __ = PaymentEventType.objects.get_or_create(
            name=event_type_name)
        # We keep a local cache of (unsaved) payment events
        event = PaymentEvent(
            event_type=event_type, amount=amount,
            reference=reference)
        return event


class Cash(BasePaymentMethod):
    def collect(self, net_amount, payment_data, * args, **kwargs):
        print("Assuming COD HAS BEEN DONE")
        return {}

    def record_payment(self, order,  net_amount, reference="", **kwargs):

        total_incl_tax = round(order.total_incl_tax, 2)
        print(net_amount, order.total_incl_tax)
        source_type, __ = SourceType.objects.get_or_create(name=PAYMENT_METHOD_CASH)
        payment_gateway_response = kwargs.get('payment_gateway_response')
        source = Source.objects.create(
            source_type=source_type,
            currency=settings.PAYMENT_CURRENCY,
            amount_allocated=net_amount,
            amount_debited=0,
            order=order,
            reference=reference)
        if payment_gateway_response:
            payment_gateway_response.sources.add(source)

        self.add_payment_event(PAYMENT_EVENT_PURCHASE, order.total_incl_tax, reference=reference)

        COD.objects.create(order=order, amount=order.total_incl_tax)


class Razorpay(BasePaymentMethod):

    def collect(self, net_amount, payment_data):
        if net_amount - int(net_amount) == 0.00:
            net_amount = int(net_amount) * 100
        else:
            net_amount = int(round(net_amount*100))
        print(net_amount)
        return RazorPayFacade().charge(
            None,
            net_amount,
            token=payment_data[RAZOR_PAY_TOKEN],
            # description=self.payment_description(order_number, total, **kwargs),
            # metadata=self.payment_metadata(order_number, total, **kwargs)
        )

    def record_payment(self, order, net_amount, reference="", **kwargs):

        source_type, __ = SourceType.objects.get_or_create(name=PAYMENT_METHOD_RAZORPAY)
        total = kwargs.get('total')
        source = Source.objects.create(
            source_type=source_type,
            currency=settings.PAYMENT_CURRENCY,
            amount_allocated=order.total_incl_tax,
            amount_debited=order.total_incl_tax,
            reference=reference,
            order=order
        )

        self.add_payment_event(PAYMENT_EVENT_PURCHASE, order.total_incl_tax)
        return source

MAP = {
    'cash': Cash,
    'razor_pay': Razorpay,
}


class Casher:

    def __init__(self, payment_data):
        """
        payment_data = {
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
        """
        self.payment_data = payment_data
        self.payment_object = None
        self.method = None
        print(payment_data)
        for method in payment_data:
            if payment_data[method]['enabled']:
                self.method = method
                self.payment_object = MAP[method]()
                break
        if self.payment_object is None:
            raise Exception("Casher - No Payment Methods are enabled.")

    def collect(self, net_payment, order):
        payment_data = self.payment_data.get(self.method)
        if order:

            response = self.payment_object.collect(net_payment, payment_data=payment_data)
            pgr = PaymentGateWayResponse.objects.create(
                transaction_id=response.get('id'),
                amount=net_payment,
                response=response,
                payment_status=True,
                order=order
            )

            source = self.payment_object.record_payment(
                order, net_payment, reference=response.get('id', '-'),
                order_number=order.id,
                payment_gateway_response=pgr            # as kwargs
            )
            pgr.source = source
            pgr.save()








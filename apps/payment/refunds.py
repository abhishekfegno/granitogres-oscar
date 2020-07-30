from django.conf import settings
from django.utils import timezone
from django.utils.module_loading import import_string


class RefundFacade(object):

    def __init__(self):
        self.payment_methods = []
        for method_config in settings.API_ENABLED_PAYMENT_METHODS:
            PaymentMethod = import_string(method_config['method'])
            self.payment_methods.append(PaymentMethod())

    def refund_order(self, order, **kwargs):
        for payment_method in self.payment_methods:

            message = f"Refund initiated against  Cancellation of Order #{order.id} " \
                      f"at {timezone.now()} via '{payment_method.name}' Payment Mode"
            payment_method.refund_order(order=order, reference=message)

    def refund_order_line(self, order, line, **kwargs):

        for payment_method in self.payment_methods:

            message = f"Refund initiated against Cancellation of Item #{line.id} X {line.quantity} " \
                      f"under Order #{order.id} " \
                      f"at {timezone.now()} via '{payment_method.name} Payment Mode"
            payment_method.refund_order_line(line=line, reference=message)

from django.conf import settings
from django.utils.module_loading import import_string
from oscar.apps.payment.models import Source


class RefundFacade(object):
    """
    Independent of payment method.

    Works in the basis of payment gateways mentioned in settings.API_ENABLED_PAYMENT_METHODS recommended  by
    package 'django-oscarapicheckout'.

    each method mentioned in methods at API_ENABLED_PAYMENT_METHODS must inherit mixin,
    'apps.payment.utils.PaymentRefundMixin'

    """
    def __init__(self):
        self.payment_methods = []
        for method_config in settings.API_ENABLED_PAYMENT_METHODS:
            PaymentMethod = import_string(method_config['method'])
            self.payment_methods.append(PaymentMethod())

    def get_sources_model_from_order(self, order):
        return Source.objects.filter(order=order).prefetch_related('source_type', 'order', 'order__line')

    def refund_order(self, order, **kwargs):

        for source in self.get_sources_model_from_order(order):
            for payment_method in self.payment_methods:
                if payment_method.name == source.source_type.name:
                    payment_method.refund_order(order=order, source=source)

    def refund_order_line(self, line, **kwargs):
        order = line.order
        for source in self.get_sources_model_from_order(order):
            for payment_method in self.payment_methods:
                if payment_method.name == source.source_type.name:
                    payment_method.refund_order_line(line=line, source=source,
                                                     quantity_to_refund=kwargs.get('quantity', line.quantity))

    def refund_admin_defined_payment(self, order, event_type, amount, lines=None,
                                     line_quantities=None, **kwargs):

        for source in self.get_sources_model_from_order(order):
            for payment_method in self.payment_methods:
                if payment_method.name == source.source_type.name:
                    return payment_method.refund_admin_defined_payment(order, event_type, amount, lines=lines,
                                                                line_quantities=line_quantities, source=source, **kwargs)



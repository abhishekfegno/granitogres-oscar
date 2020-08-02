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
        return Source.objects.filter(order=order).prefetch_related('source_type', 'order', 'order__lines')

    def refund_order(self, order, **kwargs):
        if order.status in settings.OSCAR_ORDER_REFUNDABLE_STATUS:
            return

        for source in self.get_sources_model_from_order(order):
            for payment_method in self.payment_methods:
                if payment_method.name == source.source_type.name:
                    payment_method.refund_order(order=order, source=source)

    def refund_order_line(self, line, **kwargs):
        if line.status in settings.OSCAR_LINE_REFUNDABLE_STATUS or line.active_quantity == 0:
            return
        order = line.order
        for source in self.get_sources_model_from_order(order):
            for payment_method in self.payment_methods:
                if payment_method.name == source.source_type.name:
                    payment_method.refund_order_line(line=line, source=source,
                                                     quantity_to_refund=kwargs.get('quantity', line.active_quantity))

    def refund_admin_defined_payment(self, order, event_type, amount, lines=None,
                                     line_quantities=None, **kwargs):
        _line, _qty = [], []
        for line, qty in zip(lines, line_quantities):
            if line.status not in settings.OSCAR_LINE_REFUNDABLE_STATUS or line.refunded_quantity < line.quantity:
                _line.append(line)
                _qty.append(qty)
            else:
                line.refunded_quantity = line.quantity
                line.save()
        lines = _line
        line_quantities = _qty

        if not lines:
            return

        for source in self.get_sources_model_from_order(order):
            for payment_method in self.payment_methods:
                if payment_method.name == source.source_type.name:
                    payment_method.refund_admin_defined_payment(order, event_type, amount, lines=lines,
                                                                line_quantities=line_quantities, source=source,
                                                                **kwargs)
                    break
        for line, qty in zip(lines, line_quantities):
            line.refunded_quantity += qty
            line.save()


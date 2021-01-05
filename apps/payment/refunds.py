from django.conf import settings
from django.utils.module_loading import import_string
from apps.payment.models import Source


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

    def get_sources_model_from_order(self, order, reference=''):
        source, _ = Source.objects.get_or_create(order=order, defaults={'reference': reference})
        return source

    def get_source_n_method(self, order, reference=None):
        source = self.get_sources_model_from_order(order, reference=reference)
        # there should be only one per order. and we have
        # single transactions only.
        for payment_method in self.payment_methods:
            if payment_method.name == source.source_type.name:
                return source, payment_method
                # payment_method  will be always RazorPay()
        return None, None

    def refund_order(self, order, **kwargs):
        """
        Caller Functions:
            1. EventHandler.handle_order_status_change()

        Procedure.
            ✔ 1. Order Status has already been updated. So leave it.
            ✔ 2. Get the succeeded Order State.
            ✔ 3. Create a Transaction Record
            ✔ 4. Create a PaymentEvent
        """

        if order.status not in settings.OSCAR_ORDER_REFUNDABLE_STATUS:
            """
            Handle this error before calling 'refund_order'
            """
            raise Exception(
                f"Could not Refund Order #{order.number} With Status '{order.status}'!"
            )
        source, payment_method = self.get_source_n_method(order)        # case 2 handled
        # Generate Payment_event

        return payment_method.refund_order(order=order, source=source)         # Case 3 & 4 handled
        # we are breaking the loop so as to get the first source

    def refund_order_line(self, line, **kwargs):
        # if line.status in settings.OSCAR_LINE_REFUNDABLE_STATUS:        # or line.active_quantity == 0:
        #     return
        order = line.order

        # source will be instance of <Source>
        # payment_method will be the object of <PaymentMethod: >
        source, payment_method = self.get_source_n_method(order)
        msg = f"""
        REFUNDING FOR ORDER LINE {line} ({order}).
        source : {source}
        payment_method : {payment_method}
        """
        print(msg)
        return payment_method.refund_order_line(line=line, source=source,
                                                quantity_to_refund=line.quantity)

    def refund_order_partially(self, order, lines=None, line_quantities=None, **kwargs):
        """
        refund_admin_defined_payment

        Filter out lines and quantities, get source and apyment method, then call to trigger refund.

        """
        if lines is None:
            lines = [l for l in order.lines.all()]  # make it python object.

        if line_quantities is None:
            line_quantities = [line.quantity for line in lines]
        amount = sum([line.line_price_incl_tax for line in lines])

        _lines, _qty = [], []
        for line, qty in zip(lines, line_quantities):
            if line.status not in settings.OSCAR_LINE_REFUNDABLE_STATUS:
                _lines.append(line)
                _qty.append(qty)

            # if line.status not in settings.OSCAR_LINE_REFUNDABLE_STATUS or line.refunded_quantity < line.quantity:
            #     _line.append(line)
            #     _qty.append(qty)
            # else:
            #     line.refunded_quantity = line.quantity
            #     line.save()

        if not _lines:
            return None

        lines = _lines
        line_quantities = _qty
        source, payment_method = self.get_source_n_method(order)

        return payment_method.refund_order_partially(source=source, order=order, lines=lines, amount=amount,
                                                     line_quantities=line_quantities, **kwargs)









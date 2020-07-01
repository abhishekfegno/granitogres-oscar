
from oscarapicheckout import states
from oscarapicheckout.methods import PaymentMethod


class RazorPay(PaymentMethod):
    """
    Cash payments are an example of how to implement a payment method plug-in. It
    doesn't do anything more than record a transaction and payment source.
    """
    # Translators: Description of payment method in checkout
    name = 'Razor Pay'
    code = 'razor_pay'

    def _record_payment(self, request, order, method_key, amount, reference, **kwargs):
        # import pdb;  pdb.set_trace()
        source = self.get_source(order, reference)

        amount_to_allocate = amount - source.amount_allocated
        source.allocate(amount_to_allocate, reference)

        amount_to_debit = amount - source.amount_debited
        source.debit(amount_to_debit, reference)

        event = self.make_debit_event(order, amount_to_debit, reference)
        for line in order.lines.all():
            self.make_event_quantity(event, line, line.quantity)

        return states.Complete(source.amount_debited, source_id=source.pk)





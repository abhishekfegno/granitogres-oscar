from django.conf import settings
from django.contrib import messages
from django.forms import modelform_factory
from oscar.apps.dashboard.orders.views import OrderDetailView as OscarOrderDetailView
from django.utils.translation import gettext_lazy as _

from apps.order.models import OrderNote, Order
from apps.order.processing import EventHandler
from apps.payment.refunds import RefundFacade
from lib.exceptions import AlertException

OrderSlotForm = modelform_factory(model=Order, fields=['slot'])


class OrderDetailView(OscarOrderDetailView):
    order_actions = ('save_note', 'delete_note', 'change_order_status', 'change_order_slot',
                     'create_order_payment_event')

    def change_line_statuses(self, request, order, lines, quantities):
        new_status = request.POST['new_status'].strip()
        if not new_status:
            messages.error(request, _("The new status '%s' is not valid")
                           % new_status)
            return self.reload_page()
        errors = []
        for line in lines:
            if new_status not in line.available_statuses():
                errors.append(_("'%(status)s' is not a valid new status for"
                                " line %(line_id)d") % {'status': new_status,
                                                        'line_id': line.id})
        if errors:
            for err in errors:
                messages.error(request, err)
            return self.reload_page()

        msgs = []
        print("#" * 40)
        try:
            if new_status in settings.OSCAR_LINE_REFUNDABLE_STATUS:
                event = RefundFacade().refund_order_partially(
                    order=order, lines=lines, line_quantities=quantities
                )
            for line in lines:
                msg = _("Status of line #%(line_id)d changed from '%(old_status)s'"
                        " to '%(new_status)s'") % {'line_id': line.id,
                                                   'old_status': line.status,
                                                   'new_status': new_status}
                EventHandler().handle_order_line_status_change(line, new_status, already_refunded_together=True, note_msg=msgs, note_type="Admin")
                msgs.append(msg)
                # line.set_status(new_status)
        except AlertException as ae:
            messages.error(request, str(ae))

        for msg in msgs:
            messages.info(request, msg)
        message = "\n".join(msgs)
        order.notes.create(user=request.user, message=message, note_type=OrderNote.SYSTEM)
        return self.reload_page()

    def get_order_slot_form(self):
        data = None
        if self.request.method == 'POST':
            data = self.request.POST
        return OrderSlotForm(instance=self.object, data=data)

    def change_order_slot(self, request, order):
        old_slot = order.slot.slot
        form = self.get_order_slot_form()
        if not form.is_valid():
            return self.reload_page(error=_("There are some errors in order slot form"))
        else:
            form.save()
            success_msg = _(
                "Order slot has been changed from '%(old_status)s' to "
                "'%(new_status)s'") % {'old_status': old_slot,
                                       'new_status': form.instance.slot.slot}
            messages.success(request, success_msg)
        return self.reload_page()

    def get_context_data(self, **kwargs):
        kwargs = super(OrderDetailView, self).get_context_data(**kwargs)
        kwargs['order_slot_form'] = self.get_order_slot_form()
        return kwargs




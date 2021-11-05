from django.conf import settings
from django.contrib import messages
from django.forms import modelform_factory
from oscar.apps.dashboard.orders.views import OrderDetailView as OscarOrderDetailView, OrderListView as OscarOrderListView
from django.utils.translation import gettext_lazy as _

from couriers.delhivery.facade import Delhivery
from apps.dashboard.orders.forms import OrderSearchForm
from apps.order.models import OrderNote, Order
from apps.payment.refunds import RefundFacade
from lib.exceptions import AlertException

OrderSlotForm = modelform_factory(model=Order, fields=['slot'])


class OrderListView(OscarOrderListView):
    form_class = OrderSearchForm

    def get_queryset(self):  # noqa (too complex (19))
        qs = super(OrderListView, self).get_queryset()
        data = self.form.cleaned_data
        if data['slot']:
            qs = qs.filter(slot_id=data['slot'])
        return qs



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
                if new_status == settings.ORDER_STATUS_REFUND_APPROVED:
                    d = Delhivery()
                    d.pack_return(order)
                    from apps.order.processing import EventHandler
                    eh = EventHandler()
                    note_msg = f"Return request for {len(lines)} Item(s)  Return has been approved"
                    note_msg_2 = f"Return Pickup initiated for {len(lines)} Item(s)!"
                    eh.create_note(order, message=note_msg, note_type="System")
                    eh.create_note(order, message=note_msg_2, note_type="System")

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
        old_slot = order.slot and order.slot.slot
        form = self.get_order_slot_form()
        if not form.is_valid():
            return self.reload_page(error=_("There are some errors in order slot form"))
        else:
            form.save()
            if not old_slot:
                success_msg = _(
                    "Order slot has been changed to '%(new_status)s'") % {
                                  'new_status': form.instance.slot.slot
                }
            else:
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




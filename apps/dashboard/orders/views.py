from django.conf import settings
from django.contrib import messages
from oscar.apps.dashboard.orders.views import OrderDetailView as OscarOrderDetailView
from django.utils.translation import gettext_lazy as _

from apps.order.models import OrderNote
from apps.payment.refunds import RefundFacade


class OrderDetailView(OscarOrderDetailView):

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
            messages.error(request, "\n".join(errors))
            return self.reload_page()

        msgs = []
        if new_status in settings.OSCAR_LINE_REFUNDABLE_STATUS:
            event = RefundFacade().refund_order_partially(
                order=order, lines=lines, line_quantities=quantities
            )

        for line in lines:
            msg = _("Status of line #%(line_id)d changed from '%(old_status)s'"
                    " to '%(new_status)s'") % {'line_id': line.id,
                                               'old_status': line.status,
                                               'new_status': new_status}
            msgs.append(msg)
            line.set_status(new_status)
        message = "\n".join(msgs)
        messages.info(request, message)
        order.notes.create(user=request.user, message=message,
                           note_type=OrderNote.SYSTEM)
        return self.reload_page()
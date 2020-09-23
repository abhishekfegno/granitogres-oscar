from oscar.apps.payment.admin import *  # noqa

from apps.payment.models import PaymentGateWayResponse, COD, CODRepayments

admin.site.register(PaymentGateWayResponse)
admin.site.register(COD)
admin.site.register(CODRepayments)






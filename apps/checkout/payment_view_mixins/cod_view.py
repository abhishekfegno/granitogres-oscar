from django.conf import settings
from oscar.core.loading import get_model
from oscar.templatetags.currency_filters import currency
from apps.checkout.facade.stripe import StripeFacade as Facade

from apps.checkout import forms


SourceType = get_model('payment', 'SourceType')
Source = get_model('payment', 'Source')


class CodPaymentMixin(object):


    def handle_cod(self, order_number, total, **kwargs):
        # https://github.com/jerinisready/django-oscar-cash-on-delivery/tree/master/cashondelivery
        # https://stackoverflow.com/questions/43408588/implementing-django-oscar-cod
        self.amount = float(total.excl_tax)
        gateway_code = self.request.POST.get('gateway_code', None) # noqa
        if gateway_code and gateway_code == 'cash-on-delivery':
            # Record payment source and event
            source_type, is_created = SourceType.objects.get_or_create(
                name='cash-on-delivery')
            source = source_type.sources.model(
                source_type=source_type,
                amount_allocated=total.excl_tax)
            self.add_payment_source(source) # noqa
            self.add_payment_event('CREATED', total.excl_tax) # noqa
            return


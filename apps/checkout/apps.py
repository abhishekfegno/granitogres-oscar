import oscar.apps.checkout.apps as apps
from oscar.core.loading import get_class


class CheckoutConfig(apps.CheckoutConfig):
    name = 'apps.checkout'



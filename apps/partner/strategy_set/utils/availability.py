from oscar.core.loading import get_class
from django.utils.translation import gettext_lazy as _

Unavailable = get_class('partner.availability', 'Unavailable')
StockRequired = get_class('partner.availability', 'StockRequired')


class PinCodeNotFound(Unavailable):
    message = 'no_pin_code'


class LoginRequiredToPurchase(StockRequired):
    CODE_LOGIN_REQUIRED = 'login-required'

    def is_purchase_permitted(self, quantity):
        resp = super(LoginRequiredToPurchase, self).is_purchase_permitted(quantity)
        if resp[0] is True and self.request.user.is_anonymous:
            return False, _("login required")
        return resp

    @property
    def code(self):
        """
        Code indicating availability status.
        """
        if self.request.user.is_anonymous:
            return self.CODE_LOGIN_REQUIRED
        if self.num_available > 0:
            return self.CODE_IN_STOCK
        return self.CODE_OUT_OF_STOCK

    @property
    def short_message(self):
        if self.request.user.is_anonymous:
            return _("Login Required")
        if self.num_available > 0:
            return _("In stock")
        return _("Unavailable")

    @property
    def message(self) -> str:
        """
        Full availability text, suitable for detail pages.
        """
        if self.request.user.is_anonymous:
            return _("You need to login to buy an item.")
        if self.num_available > 0:
            return _("In stock (%d available)") % self.num_available
        return _("Unavailable")

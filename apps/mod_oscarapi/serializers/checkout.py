from oscarapicheckout.serializers import (
    CheckoutSerializer as OscarAPICheckoutSerializer,
    PaymentMethodsSerializer as OscarAPIPaymentMethodsSerializer,
)


class PaymentMethodsSerializer(OscarAPIPaymentMethodsSerializer):
    """
    Should not Remove this.
    Dependiences Created.
    """
    pass


class CheckoutSerializer(OscarAPICheckoutSerializer):
    """
    Should not Remove this.
    Dependiences Created.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['payment'] = PaymentMethodsSerializer(context=self.context)



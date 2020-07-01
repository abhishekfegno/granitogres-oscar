from oscar.core.loading import get_model
from rest_framework import serializers
from oscar.core.loading import get_model
from oscarapicheckout.serializers import PaymentMethodsSerializer
from oscarapicheckout.serializers import (
    CheckoutSerializer as OscarAPICheckoutSerializer,
)

Basket = get_model('basket', 'Basket')


class CheckoutSerializer(OscarAPICheckoutSerializer):
    """
    Should not Remove this.
    Dependiences Created.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Build PaymentMethods field
        self.fields['payment'] = PaymentMethodsSerializer(context=self.context)
        # We require a request because we need to know what accounts are valid for the
        # user to be drafting from. This is derived from the user when authenticated or
        # the session store when anonymous
        request = self.context.get('request', None)
        assert request is not None, (
                "`%s` requires the request in the serializer"
                " context. Add `context={'request': request}` when instantiating "
                "the serializer." % self.__class__.__name__
        )

        view = self.context.get('view', None)
        assert view is not None, (
                "`%s` requires the view in the serializer "
                " context. Add `context={'request': request, 'view': self}` when instantiating "
                "the serializer." % self.__class__.__name__
        )

        # Limit baskets to only the one that is active and owned by the user.
        # basket = get_basket(request)
        self.fields['basket'].queryset = Basket.objects.filter(
            owner=request.user,
            status=Basket.BUY_NOW,
            id=view.kwargs[view.kwargs_basket_key])





from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
from oscar.core.loading import get_model
from oscarapi.basket import operations
from oscarapi.utils.loading import get_api_classes, get_api_class
from oscarapi.views.utils import BasketPermissionMixin
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.api_set.serializers.basket import WncBasketSerializer

Basket = get_model("basket", "Basket")
Line = get_model("basket", "Line")


@api_view()
def get_basket(request):
    serializer_class = WncBasketSerializer
    basket = operations.get_basket(request)
    ser = serializer_class(basket, context={"request": request})
    return Response(ser.data)


















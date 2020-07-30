from oscarapi.basket import operations
from rest_framework.decorators import api_view
from rest_framework.response import Response
from apps.api_set.serializers.basket import WncBasketSerializer


@api_view()
def get_basket(request):
    serializer_class = WncBasketSerializer
    basket = operations.get_basket(request)
    ser = serializer_class(basket, context={"request": request})
    return Response(ser.data)




















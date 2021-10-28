from oscarapi.basket import operations
from rest_framework.decorators import api_view
from rest_framework.response import Response
from apps.api_set.serializers.basket import WncBasketSerializer
from apps.order.models import TimeSlot


@api_view()
def get_basket(request):
    serializer_class = WncBasketSerializer
    basket = operations.get_basket(request)
    ser = serializer_class(basket, context={"request": request})
    out = ser.data
    # import pdb;pdb.set_trace()
    try:
        TimeSlot.get_upcoming_slots()
    except ZeroDivisionError:
        return Response(out)
    upcoming_slots = [slot.to_dict() for slot in TimeSlot.get_upcoming_slots()]
    # import pdb;pdb.set_trace()
    upcoming_slots[0]['is_next'] = True
    out["available_deliveries"] = upcoming_slots
    return Response(out)




















from oscarapi.basket import operations
from rest_framework.decorators import api_view
from rest_framework.response import Response
from apps.api_set.serializers.basket import WncBasketSerializer
from apps.order.models import TimeSlot


@api_view()
def get_basket(request):
    print("########## Point 01")
    serializer_class = WncBasketSerializer
    basket = operations.get_basket(request)
    print("########## Point 02")
    ser = serializer_class(basket, context={"request": request})
    out = ser.data
    print("########## Point 03")

    # import pdb;pdb.set_trace()
    try:
        print("########## Point 04")
        # TimeSlot.get_upcoming_slots()
        print("########## Point 05")
    except ZeroDivisionError:
        print("########## Point 06")
        return Response(out)
    print("########## Point 07")
    # upcoming_slots = [slot.to_dict() for slot in TimeSlot.get_upcoming_slots()]
    # import pdb;pdb.set_trace()
    # upcoming_slots[0]['is_next'] = True
    # out["available_deliveries"] = upcoming_slots
    out["available_deliveries"] = []
    print("########## Point 08")
    return Response(out)




















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
    upcoming_slots = [{
        'pk': slot.pk,
        'start_time': slot.config.start_time,
        'end_time': slot.config.end_time,
        'start_date': slot.start_date,
        'max_datetime_to_order': slot.max_datetime_to_order,
        'is_next': False,
        'index': slot.index,
    } for slot in TimeSlot.get_upcoming_slots()]
    upcoming_slots[0]['is_next'] = True
    out["available_deliveries"] = upcoming_slots
    return Response(out)




















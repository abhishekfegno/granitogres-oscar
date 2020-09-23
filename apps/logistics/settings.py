from django.conf import settings


# you can change this to agent model,  if you have some external delivery partner.
AGENT_MODEL = settings.AUTH_USER_MODEL

LOGISTICS_CONSIGNMENT_CREATE_STATUS_FOR_ORDER = settings.ORDER_STATUS_CONFIRMED
LOGISTICS_CONSIGNMENT_CREATE_STATUS_FOR_ORDER_LINE_RETURN = settings.ORDER_STATUS_RETURN_APPROVED

LOGISTICS_CONSIGNMENT_DESTROY_STATUS_FOR_ORDER_LINE_RETURN_CANCELLED = settings.ORDER_STATUS_RETURN_REQUESTED
LOGISTICS_ORDER_STATUS_ON_TRIP_ACTIVATE = settings.ORDER_STATUS_OUT_FOR_DELIVERY








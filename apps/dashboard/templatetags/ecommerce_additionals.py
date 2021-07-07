from django import template
register = template.Library()


@register.filter
def mod(value, arg):
    try:
        return int(value) % int(arg) == 0
    except (ValueError, ZeroDivisionError):
        return False


@register.filter
def get_slots_from_deliverable_consignments(consignments):
    out = {}
    for cons in consignments:
        if cons.order.slot and cons.order.slot not in out:
            out[cons.order.slot] = 1
    return out.keys()


@register.filter
def get_slots_from_return_consignments(consignments):
    out = {}
    for cons in consignments:
        if cons.order_line and cons.order_line.order.slot and cons.order_line.order.slot not in out:
            out[cons.order.slot] = 1
    return out.keys()


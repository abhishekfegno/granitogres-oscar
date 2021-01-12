from django import template
register = template.Library()

@register.filter
def mod(value, arg):
    try:
        return int(value) % int(arg) == 0
    except (ValueError, ZeroDivisionError):
        return False

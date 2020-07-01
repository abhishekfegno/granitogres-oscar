from django import template

from apps.users.models import GSTNumber

register = template.Library()


@register.simple_tag
def gst(user):
    return GSTNumber.get_gst(user)

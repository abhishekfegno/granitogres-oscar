from django.db.models.signals import post_save
from django.dispatch import receiver
from oscar.apps.dashboard.ranges.models import *  # noqa isort:skip

from apps.mod_oscarapi.serializers.product import Range
from django.core.cache import cache


@receiver(post_save, sender=Range)
def clear_cache_range(sender, instance, created, **kwargs):
    range_slugs = [
        'exclusive-products',
        'furnitures-for-your-home',
        'jumbo-offer',
        'offer-banner-x3',
        'customer-favorites'
    ]
    if instance.slug in range_slugs:
        print("Clearing Range slug cache")
        cache.delete_pattern('apps.api_set_v2.views.index?zone*')



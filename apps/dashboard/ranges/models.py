from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from oscar.apps.dashboard.ranges.models import *  # noqa isort:skip

from django.core.cache import cache
from oscar.core.loading import get_model
# AbstractRange = get_model('offer', 'AbstractRange')
Range = get_model('offer', 'Range')

# class Range(AbstractRange):
#     # search_tags = models.TextField(null=True, blank=True)
#     seo_title = models.CharField(max_length=120, null=True, blank=True)
#     seo_description = models.CharField(max_length=255, null=True, blank=True)
#     seo_keywords = models.CharField(max_length=255, null=True, blank=True)
#     search_tags = models.TextField(null=True, blank=True)
#     ogmail = models.CharField(max_length=255, null=True, blank=True)


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



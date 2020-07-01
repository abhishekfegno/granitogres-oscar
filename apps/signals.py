from django.contrib.postgres.search import SearchVector
from django.db.models.signals import post_save
from django.dispatch import receiver
from oscar.core.loading import get_model

from apps.catalogue.models import StockRecord, Product


@receiver(post_save, sender=StockRecord)
def update_product_rate_and_cache(sender, instance, **kwargs):
    instance.product._save_price()
    instance.product.save()
    instance.product.clear_list_caches()


@receiver(post_save, sender=Product)
def update_search_vector(sender, instance, **kwargs):
    Product.objects.filter(pk=instance.pk).update(
        search=SearchVector('title', weight='A') + SearchVector('description', weight='D')
    )


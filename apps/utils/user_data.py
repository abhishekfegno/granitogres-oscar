from allauth.account.models import EmailAddress
from django.core.cache import cache

from lib import cache_key
from lib.cache import cache_library


def have_email_activated(user):

    if cache_key.have_email_activated__cache_key not in cache:
        cache.set(cache_key.have_email_activated__cache_key, [])
    users_with_email = cache.get(cache_key.have_email_activated__cache_key)
    if user.id not in users_with_email:
        email_verified = EmailAddress.objects.filter(user=user, verified=True).exists()
        if not email_verified:
            return False
        users_with_email.append(user.id)
        cache.set(cache_key.have_email_activated__cache_key, users_with_email)
    return True


def have_shipping_address(user):
    def _inner():
        nonlocal user
        user.addresses.all().exists()
        return

    return cache_library(
        cache_key.have_shipping_address__cache_key,
        cb=_inner,
    )

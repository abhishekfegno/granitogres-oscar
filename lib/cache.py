from django.conf import settings
from django.core.cache import cache
from oscar.core.loading import get_model

from lib import cache_key


def cache_library(key, user, cb=None, default=None, ttl=settings.DEFAULT_CACHE_TTL):
    """
    Cache Manager for Project.
    :key: = key of cache.
    :cb: = callback function to generate data if key fails to find.
    :default: = alternative to callback to get default data to set in cache and return.
    """
    if user:
        cache.clear()
        value = cb()
        value['user'] = user
        cache.set(key, value)
    if key in cache:
        c = cache.get(key)
        if c or not (cb and default):
            return c    # return <c> or <None> depends on unavailablity of cb or default
    if not cb:
        cb = lambda: default
    value = cb()
    cache.set(key, value)
    return value


def get_featured_path():
    def _inner():
        Category = get_model('catalogue', 'Category')
        featured = Category.get_root_nodes().filter(slug=settings.FEATURED_CATEGORY_SLUG).first()
        if not featured:
            featured = Category.add_root(name=settings.FEATURED_CATEGORY_SLUG, slug=settings.FEATURED_CATEGORY_SLUG)
        return featured.path
    return cache_library(cache_key.featured_category__cache_key, cb=_inner)




import oscar.apps.catalogue.apps as apps
from django.conf import settings


class CatalogueConfig(apps.CatalogueConfig):
    name = 'apps.catalogue'

    def ready(self):
        super(CatalogueConfig, self).ready()
        from oscar.core.loading import get_model
        Category = get_model('catalogue', 'Category')
        if not Category.get_root_nodes().filter(slug=settings.FEATURED_CATEGORY_SLUG).exists():
            Category.add_root(name=settings.FEATURED_CATEGORY_SLUG, slug=settings.FEATURED_CATEGORY_SLUG)


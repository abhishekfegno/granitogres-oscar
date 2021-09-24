import oscar.apps.catalogue.reviews.apps as apps


class CatalogueReviewsConfig(apps.CatalogueReviewsConfig):
    name = 'apps.catalogue.reviews'

    def ready(self):
        super(CatalogueReviewsConfig, self).ready()

# from oscar.apps.basket.abstract_models import AbstractBasket
from django.db import IntegrityError

from apps.buynow.basket_utils.models import AbstractBuyNowBasket


class Basket(AbstractBuyNowBasket):
    """
    Moking up the real basket
    """

    def add_product(self, product, quantity=1, options=None):
        try:
            line, created = super(Basket, self).add_product(product, quantity=quantity, options=options)
        except IntegrityError as e:
            pass
        else:
            if line.quantity <= 0:
                line.delete()
            self.reset_offer_applications()
            return line, created
    add_product.alters_data = True
    add = add_product

    @property
    def sorted_recommended_products(self):
        """Keeping order by recommendation ranking."""
        return [r.recommendation for r in self.primary_recommendations
                                              .select_related('recommendation').all()]

from oscar.apps.basket.models import *  # noqa isort:skip



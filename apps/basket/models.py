# from oscar.apps.basket.abstract_models import AbstractBasket
from django.conf import settings
from django.db import IntegrityError

from apps.buynow.basket_utils.models import AbstractBuyNowBasket


class Basket(AbstractBuyNowBasket):
    """
    Moking up the real basket
    """

    def add_product(self, product, quantity=1, options=None):
        """
        Add a product to the basket

        The 'options' list should contains dicts with keys 'option' and 'value'
        which link the relevant product.Option model and string value
        respectively.

        Returns (line, created).
          line: the matching basket line
          created: whether the line was created or updated

        """
        if options is None:
            options = []
        if not self.id:
            self.save()

        if quantity > settings.OSCAR_MAX_PER_LINE_QUANTITY:
            raise ValueError(
                "You could not add more than %d items of %s in the same order" % (settings.OSCAR_MAX_PER_LINE_QUANTITY, product))

        # Ensure that all lines are the same currency
        price_currency = self.currency
        stock_info = self.get_stock_info(product, options)

        if not stock_info.price.exists:
            raise ValueError(
                "Strategy hasn't found a price for product %s" % product)

        if price_currency and stock_info.price.currency != price_currency:
            raise ValueError((
                                 "Basket lines must all have the same currency. Proposed "
                                 "line has currency %s, while basket has currency %s")
                             % (stock_info.price.currency, price_currency))

        if stock_info.stockrecord is None:
            raise ValueError((
                                 "Basket lines must all have stock records. Strategy hasn't "
                                 "found any stock record for product %s") % product)

        # Line reference is used to distinguish between variations of the same
        # product (eg T-shirts with different personalisations)
        line_ref = self._create_line_reference(
            product, stock_info.stockrecord, options)

        # Determine price to store (if one exists).  It is only stored for
        # audit and sometimes caching.
        defaults = {
            'quantity': quantity,
            'price_excl_tax': stock_info.price.excl_tax,
            'price_currency': stock_info.price.currency,
        }
        if stock_info.price.is_tax_known:
            defaults['price_incl_tax'] = stock_info.price.incl_tax

        line, created = self.lines.get_or_create(
            line_reference=line_ref,
            product=product,
            stockrecord=stock_info.stockrecord,
            defaults=defaults)
        if created:
            for option_dict in options:
                line.attributes.create(option=option_dict['option'],
                                       value=option_dict['value'])
        else:
            net_qty = max(0, line.quantity + quantity)
            if 0 > net_qty > settings.OSCAR_MAX_PER_LINE_QUANTITY:
                raise ValueError(
                    "You could not add more than %d items of %s in the same order" % (
                    settings.OSCAR_MAX_PER_LINE_QUANTITY, product))

            line.quantity = net_qty
            if net_qty > 0:
                line.save()
            else:
                line.delete()
        self.reset_offer_applications()

        # Returning the line is useful when overriding this method.
        return line, created

    add_product.alters_data = True
    add = add_product

    @property
    def sorted_recommended_products(self):
        """Keeping order by recommendation ranking."""
        return [r.recommendation for r in self.primary_recommendations
                                              .select_related('recommendation').all()]

from oscar.apps.basket.models import *  # noqa isort:skip



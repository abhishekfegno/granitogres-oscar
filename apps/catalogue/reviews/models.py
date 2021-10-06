from django.db import models
from oscar.apps.catalogue.reviews.abstract_models import (
    AbstractProductReview, AbstractVote)
from oscar.core.loading import is_model_registered
from django.utils.translation import gettext_lazy as _
from django.conf import settings

if not is_model_registered('reviews', 'Vote'):
    class Vote(AbstractVote):
        pass


class ProductReview(AbstractProductReview):

    @property
    def date(self):
        return self.date_created.strftime("%Y-%m-%d")

    def __str__(self):
        return f"{self.product.name} | {self.title}"


class ProductReviewImage(models.Model):
    review = models.ForeignKey(
        ProductReview,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name=_("Product"))
    original = models.ImageField(
        _("Original"), upload_to=settings.OSCAR_IMAGE_FOLDER, max_length=255)
    caption = models.CharField(_("Caption"), max_length=200, blank=True)

    #: Use display_order to determine which is the "primary" image
    display_order = models.PositiveIntegerField(
        _("Display order"), default=0, db_index=True,
        help_text=_("An image with a display order of zero will be the primary"
                    " image for a product"))
    date_created = models.DateTimeField(_("Date created"), auto_now_add=True)

    class Meta:
        app_label = 'reviews'
        # Any custom models should ensure that this ordering is unchanged, or
        # your query count will explode. See AbstractProduct.primary_image.
        ordering = ["display_order"]
        verbose_name = _('Product review image')
        verbose_name_plural = _('Product reviewimages')

    def __str__(self):
        return "Image of '%s'" % self.review

    def is_primary(self):
        """
        Return bool if image display order is 0
        """
        return self.display_order == 0

    def delete(self, *args, **kwargs):
        """
        Always keep the display_order as consecutive integers. This avoids
        issue #855.
        """
        super().delete(*args, **kwargs)
        for idx, image in enumerate(self.review.images.all()):
            image.display_order = idx
            image.save()


from oscar.apps.catalogue.reviews.models import *  # noqa isort:skip

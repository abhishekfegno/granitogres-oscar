from django.db import models
from django.db.models import F, Count
from django.db.models.signals import post_save
from django.dispatch import receiver
from oscar.apps.catalogue.reviews.abstract_models import (
    AbstractProductReview, AbstractVote)
from oscar.core import validators
from oscar.core.loading import is_model_registered
from django.utils.translation import gettext_lazy as _, pgettext_lazy
from django.conf import settings

if not is_model_registered('reviews', 'Vote'):
    class Vote(AbstractVote):
        pass


class ProductReview(AbstractProductReview):
    SCORE_CHOICES = tuple([(x, x) for x in range(0, 6)])
    score = models.SmallIntegerField(_("Score"), choices=SCORE_CHOICES)

    title = models.CharField(
        verbose_name=pgettext_lazy("Product review title", "Title"),
        max_length=255, validators=[validators.non_whitespace], null=True, blank=True)

    body = models.TextField(_("Body"), null=True, blank=True)

    order_line = models.ForeignKey('order.Line', related_name='review_set', null=True, on_delete=models.CASCADE)

    @property
    def date(self):
        return self.date_created.strftime("%Y-%m-%d")

    def __str__(self):
        return f"{self.product.name} | {self.title}"

    class Meta:
        ordering = ('-total_votes', '-delta_votes')


class ProductReviewImage(models.Model):
    review = models.ForeignKey(
        ProductReview,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name=_("Product"))
    original = models.FileField(
        _("Original"), upload_to='review-media/', max_length=255)
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



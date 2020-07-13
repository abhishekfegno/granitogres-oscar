# /home/jk/code/grocery/apps/dashboard/custom/models.py

from django.core import validators
from django.db import models
from django.urls import reverse
from sorl.thumbnail import get_thumbnail

from apps.utils import image_not_found


class empty:
    def build_absolute_uri(self, path):
        return path


class OfferBanner(models.Model):

    MODEL_CHOICES = [
        ('home_page', 'Display on Home Page'),
        ('offer_page_top', 'Offer Page Top Lengthy Banner'),
        ('offer_page_middle', 'Offer Page Middle Short Banner'),
        ('offer_page_bottom', 'Offer Page Bottom Lengthy Banner'),
    ]

    display_area = models.CharField(max_length=30, choices=MODEL_CHOICES)
    position = models.PositiveSmallIntegerField(
        default=1,
        help_text="In which slider this image should be placed in design.",
        validators=[validators.MinValueValidator(1), validators.MaxValueValidator(2), ]
    )
    banner = models.ImageField(upload_to='offer-banners/')
    product_range = models.ForeignKey('offer.Range', on_delete=models.SET_NULL, blank=True, null=True)

    @property
    def redirect_to_order(self):
        return not (self.product_range and self.product_range.all_products().exists())

    def products(self):
        return self.product_range.all_products()

    def get_absolute_url(self):
        return reverse('dashboard-offer-banner-detail', kwargs={'pk': self.pk})

    def mobile_wide_image(self, width_part,  request=empty()):
        """
        120x100, 120x150, 120x300
        """
        assert width_part in ['1:3', '1:2', '1:1'], \
            f"select An appropreate width_part in mobile_wide_image({width_part}, request={request}); select from " \
            f"['1:3', '1:2', '1:1']"

        resolution = {
            '1:3': '100x120',
            '1:2': '150x120',
            '1:1': '300x120',
        }[width_part]
        return request.build_absolute_uri(
            get_thumbnail(
                self.banner, resolution, crop='center', quality=98
            ).url)






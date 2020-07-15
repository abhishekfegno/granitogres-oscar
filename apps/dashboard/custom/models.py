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
    HOME_PAGE = 'home_page'
    OFFER_TOP = 'offer_page_top'
    OFFER_MIDDLE = 'offer_page_middle'
    OFFER_BOTTOM = 'offer_page_bottom'
    MODEL_CHOICES = [
        (HOME_PAGE, 'Display on Home Page'),
        (OFFER_TOP, 'Offer Page Top Lengthy Banner'),
        (OFFER_MIDDLE, 'Offer Page Middle Short Banner'),
        (OFFER_BOTTOM, 'Offer Page Bottom Lengthy Banner'),
    ]

    POSITION_CHOICES = [
        (1, 'Slot 1'),
        (2, 'Slot 2')
    ]

    display_area = models.CharField(max_length=30, choices=MODEL_CHOICES, default=MODEL_CHOICES[1][0])
    position = models.PositiveSmallIntegerField(
        default=POSITION_CHOICES[0][0],
        choices=POSITION_CHOICES,
        help_text="In which slider slot this image should be placed in design, "
                  "adding multiple banners in same slot will show as slider in that position",
        validators=[validators.MinValueValidator(1), validators.MaxValueValidator(2), ]
    )
    banner = models.ImageField(upload_to='offer-banners/')
    product_range = models.ForeignKey('offer.Range', on_delete=models.SET_NULL, blank=False, null=True)

    @property
    def redirect_to_order(self):
        return not (self.product_range and self.product_range.all_products().exists())

    def products(self):
        return self.product_range.all_products()

    def get_absolute_url(self):
        return reverse('dashboard-custom:dashboard-offer-banner-detail', kwargs={'pk': self.pk})

    def mobile_wide_image(self, width_part,  request=empty()):
        """
        120x100, 120x150, 120x300
        """
        assert width_part in ['1:2', '1:1'], \
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






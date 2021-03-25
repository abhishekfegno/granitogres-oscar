# /home/jk/code/grocery/apps/dashboard/custom/models.py

from django.core import validators
from django.db import models
from django.urls import reverse
from sorl.thumbnail import get_thumbnail

from apps.utils import image_not_found


class empty:

    def __init__(self, **kwargs):
        for key in kwargs:
            setattr(self, key, kwargs[key])

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
        (2, 'Slot 2'),
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
    partner = models.ForeignKey('partner.Partner', on_delete=models.SET_NULL, blank=False, null=True)

    @property
    def redirect_to_order(self):
        return not (self.product_range and self.product_range.all_products().exists())

    def products(self):
        return self.product_range.all_products()

    def get_absolute_url(self):
        return reverse('dashboard-custom:dashboard-offer-banner-detail', kwargs={'pk': self.pk})

    def mobile_wide_image(self, request=empty()):
        """
        120x100, 120x150, 120x300
        """
        resolution = {
            self.OFFER_MIDDLE: '300x240',
            self.OFFER_TOP: '600x240',
            self.OFFER_BOTTOM: '600x240',
            self.HOME_PAGE: '600x240',
        }[self.display_area]

        return request.build_absolute_uri(
            get_thumbnail(self.banner, resolution, crop='center', quality=98).url
        )


class AbstractCURDModel(models.Model):
    position = models.PositiveSmallIntegerField(
        default=10,
        help_text="Larger the number, higher will be the priority")
    title = models.CharField(max_length=256, null=True, )
    subtitle = models.TextField(null=True, blank=True)

    def products(self):
        return self.product_range.all_products()

    def get_absolute_url(self):
        return reverse(self.rev_name, kwargs={'pk': self.pk})

    @property
    def referrer(self):
        raise NotImplementedError()

    @property
    def rev_name(self):
        return f'dashboard-custom:dashboard-{self.referrer}-detail'

    class Meta:
        ordering = ('-position', 'id')
        abstract = True


class ReturnReason(AbstractCURDModel):
    referrer = 'return-reason'

    def get_absolute_url(self):
        return reverse(self.rev_name, kwargs={'pk': self.pk})


class HomePageMegaBanner(AbstractCURDModel):
    referrer = 'home-page-mega-banner'
    banner = models.ImageField(upload_to='home-banner-images', help_text="Recommended : '1920x690'")
    product_range = models.ForeignKey('offer.Range', on_delete=models.CASCADE,
                                      related_name='home_banners_included_this')

    def home_banner_wide_image(self, request=empty()):
        return request.build_absolute_uri(
            get_thumbnail(self.banner, '1920x690', crop='center', quality=98).url
        )


#
# class FAQ(AbstractCURDModel):
#     referrer = 'faq'
#
#     def get_absolute_url(self):
#         return reverse(self.rev_name, kwargs={'pk': self.pk})
#
#
# class BlogTag(AbstractCURDModel):
#     referrer = 'blog-tags'
#
#
# class BlogInsight(AbstractCURDModel):
#     referrer = 'expert-tips'
#     slug = AutoSlugField(populate_from='title', unique=True, overwrite=True, max_length=256, )
#     cover_image = models.ImageField(upload_to='blog-cover-images', null=True, blank=True)
#     subtitle = models.TextField(name='subtitle', null=True, blank=True, verbose_name='Content')
#     tags = models.ManyToManyField(BlogTag, blank=True, related_name='blogs')
#     created_at = models.DateTimeField(auto_now_add=True)
#     related_products = models.ManyToManyField('catalogue.Product', blank=True, related_name='blogs')
#     related_blogs = models.ManyToManyField('self', blank=True, related_name='referred_blogs')
#
#     def related_insights(self):
#         return list(set(self.related_blogs.all() | self.referred_blogs.all()))
#
#     @property
#     def banner(self):
#         return self.cover_image
#
#
# class ContactUsEnquiry(AbstractCURDModel):
#     referrer = 'enquiries'
#     position = None
#     title = models.CharField(name='name', max_length=256, null=True, verbose_name='Name')
#     subtitle = models.TextField(name='message', null=True, blank=True, verbose_name='Message')
#     email = models.EmailField(null=True, blank=True)
#     mobile_number = models.CharField(max_length=36, null=True, blank=True)
#     user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
#     product = models.ForeignKey('catalogue.Product', on_delete=models.SET_NULL, null=True, blank=True)
#     resolved = models.BooleanField(default=False)
#     created_at = models.DateTimeField(auto_now_add=True)
#
#     @property
#     def compose_gmail_url(self):
#         message = f"""Hi {self.title}, \n\n
#
#         I am Danish from {settings.OSCAR_SHOP_NAME}. Thank You for the enquiry with us.\n
#         I have Gone through your enquiry at our contact us form.  \n
#         \n
#         =========================================\n
#         \n
#         Thank You,\n
#         With Love, \n
#         Danish,\n
#         {settings.OSCAR_SHOP_NAME}.\n
#         """
#         subject = f"[ {settings.OSCAR_SHOP_NAME} ] Response to your Enquiry ."
#         to = f"{self.email or getattr(self.user, 'email') if self.user else '-'}"
#         return f"https://mail.google.com/mail/?view=cm&fs=1&to={to}&su={subject}&body={message}"
#
#     @property
#     def mark_as_resoved(self):
#         return ""
#
#     def get_absolute_url(self):
#         return reverse(self.rev_name, kwargs={'pk': self.pk})
#
#     class Meta:
#         ordering = ('resolved', 'id',)
#         verbose_name = "Contact Us Enquiry"
#         verbose_name_plural = "Contact Us Enquiries"
#

# models_list = (FAQ, HomePageMegaBanner, OfferBanner, ContactUsEnquiry, BlogTag, BlogInsight)

models_list = (ReturnReason, HomePageMegaBanner,)

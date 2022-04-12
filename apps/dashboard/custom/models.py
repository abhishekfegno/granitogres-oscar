# /home/jk/code/grocery/apps/dashboard/custom/models.py
from datetime import timedelta

from django.conf import settings
from django.core import validators
from django.db import models
from django.db.models.signals import post_save
from django.urls import reverse
from oscar.apps.offer.models import Range
from oscar.models.fields import AutoSlugField
from solo.models import SingletonModel
from sorl.thumbnail import get_thumbnail

from apps.utils.pushnotifications import NewOfferPushNotification
from ckeditor.fields import RichTextField


class empty:

    def __init__(self, **kwargs):
        for key in kwargs:
            setattr(self, key, kwargs[key])

    def build_absolute_uri(self, path):
        return path


THUMB_QUALITY = 30
USE_ORIGINAL = False


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
    reason_type = models.CharField(max_length=256, default='return', choices=[
        ('return', 'Return'),
        ('cancel', 'Cancel'),
    ])
    referrer = 'return-reason'

    def get_absolute_url(self):
        return reverse(self.rev_name, kwargs={'pk': self.pk})


class TopCategory(AbstractCURDModel):

    image = models.ImageField(upload_to='top-category')
    product_range = models.ForeignKey('offer.Range', on_delete=models.CASCADE)
    slug = AutoSlugField(populate_from=('title', ))
    subtitle = ''
    referrer = 'top-category'
    original_resolution = "491x306"
    thumbnail_resolution = "49x30"
    
    def get_absolute_url(self):
        return reverse(self.rev_name, kwargs={'pk': self.pk})

    def serialize(self, request=empty()):
        if USE_ORIGINAL:
            abs_img = request.build_absolute_uri(self.image.url)
        else:
            abs_img = request.build_absolute_uri(get_thumbnail(self.image, self.original_resolution, quality=100, progressive=True).url)
        tmp_img = request.build_absolute_uri(get_thumbnail(self.image, self.thumbnail_resolution, quality=THUMB_QUALITY).url)
        return {
            'id': self.pk,
            'image': abs_img,
            'thumbnail': tmp_img,
            'slug': self.product_range.slug,
            'title': self.title,
            'range': self.product_range_id
        }


class OfferBox(AbstractCURDModel):
    image = models.ImageField(upload_to='top-category')
    product_range = models.ForeignKey('offer.Range', on_delete=models.CASCADE)
    slug = AutoSlugField(populate_from=('title', ))
    subtitle = ''
    referrer = 'offer-box'

    def get_absolute_url(self):
        return reverse(self.rev_name, kwargs={'pk': self.pk})

    original_resolution = "220x220"
    thumbnail_resolution = "22x22"

    def serialize(self, request=empty()):
        if USE_ORIGINAL:
            abs_img = request.build_absolute_uri(self.image.url)
        else:
            abs_img = request.build_absolute_uri(get_thumbnail(self.image, self.original_resolution, quality=100).url)

        tmp_img = request.build_absolute_uri(get_thumbnail(self.image, self.thumbnail_resolution, quality=THUMB_QUALITY).url)

        return {
            'id': self.pk,
            'image': abs_img,
            'thumbnail': tmp_img,
            'slug': self.slug,
            'title': self.title,
            'range': self.product_range_id
        }


class InAppBanner(AbstractCURDModel):
    referrer = 'in-app-banner'
    SLIDER_BANNER = "Slider"
    FULL_SCREEN_BANNER = "Full Screen"
    BANNER_TYPE = [
        (SLIDER_BANNER, SLIDER_BANNER),
        (FULL_SCREEN_BANNER, FULL_SCREEN_BANNER),
    ]
    product_range = models.ForeignKey('offer.Range', on_delete=models.CASCADE, blank=False, null=False)
    banner = models.ImageField(upload_to='offer-banners/')
    type = models.CharField(max_length=20, choices=BANNER_TYPE, default=BANNER_TYPE[0][1])

    def __str__(self):
        return f'{self.title} {self.type}'

    def get_absolute_url(self):
        return reverse(self.rev_name, kwargs={'pk': self.pk})

    def home_banner_wide_image(self, request=empty()):
        if self.type == self.SLIDER_BANNER:
            return request.build_absolute_uri(
                get_thumbnail(self.banner, settings.SHORT_SCREEN_BANNER_IMAGE_SIZE, crop='center', quality=100).url
            )

        return request.build_absolute_uri(
            get_thumbnail(self.banner, settings.WIDE_SCREEN_BANNER_IMAGE_SIZE, crop='center', quality=100).url
        )


class InAppBannerManager(models.Manager):

    def __init__(self, type_filter):
        self.type_filter = type_filter
        super().__init__()

    def get_queryset(self):
        return super().get_queryset().filter(type=self.type_filter)


class AbstractInAppBanner(InAppBanner):
    type_filter = InAppBanner.FULL_SCREEN_BANNER

    def save(self, **kwargs):
        self.type = self.type_filter
        super(AbstractInAppBanner, self).save(**kwargs)

    class Meta:
        proxy = True


class InAppFullScreenBanner(AbstractInAppBanner):
    referrer = 'in-app-full-screen-banner'
    type_filter = InAppBanner.FULL_SCREEN_BANNER
    objects = InAppBannerManager(type_filter=type_filter)

    class Meta:
        proxy = True

    original_resolution = "1920x442"
    thumbnail_resolution = "58x11"

    def serialize(self, request=empty()):
        if USE_ORIGINAL:
            abs_img = request.build_absolute_uri(self.banner.url)
        else:
            abs_img = request.build_absolute_uri(get_thumbnail(self.banner, self.original_resolution, quality=100).url)
        tmp_img = request.build_absolute_uri(get_thumbnail(self.banner, self.thumbnail_resolution, quality=THUMB_QUALITY).url)

        return {
            'id': self.pk,
            'image': abs_img,
            'thumbnail': tmp_img,
            'slug': self.pk,
            'title': self.title,
            'range': self.product_range_id
        }


class InAppSliderBanner(AbstractInAppBanner):
    referrer = 'in-app-slider-banner'
    type_filter = InAppBanner.SLIDER_BANNER
    objects = InAppBannerManager(type_filter=type_filter)

    class Meta:
        proxy = True

    original_resolution = '348x348'
    thumbnail_resolution = '34x34'

    def serialize(self, request=empty()):
        if USE_ORIGINAL:
            abs_img = request.build_absolute_uri(self.banner.url)
        else:
            abs_img = request.build_absolute_uri(get_thumbnail(self.banner, self.original_resolution, quality=100).url)
        tmp_img = request.build_absolute_uri(get_thumbnail(self.banner, self.thumbnail_resolution, quality=THUMB_QUALITY).url)

        return {
            'id': self.pk,
            'image': abs_img,
            'thumbnail': tmp_img,
            'slug': self.pk,
            'title': self.title,
            'range': self.product_range_id
        }


class HomePageMegaBanner(AbstractCURDModel):
    referrer = 'home-page-mega-banner'
    banner = models.ImageField(upload_to='home-banner-images', help_text="Recommended : '1920x690'")
    product_range = models.ForeignKey('offer.Range', on_delete=models.CASCADE,
                                      related_name='home_banners_included_this')

    def home_banner_wide_image(self, request=empty()):
        return request.build_absolute_uri(self.banner.url)
        # return request.build_absolute_uri(
        #     get_thumbnail(self.banner, settings.WIDE_SCREEN_BANNER_IMAGE_SIZE, crop='center', quality=100).url
        # )

    def home_banner_wide_image_thumbnail(self, request=empty()):
        return request.build_absolute_uri(
            get_thumbnail(self.banner, settings.WIDE_SCREEN_BANNER_THUMBNAIL_SIZE, crop='center', quality=100).url
        )


class SocialMediaPost(AbstractCURDModel):
    referrer = 'social-media'
    banner = models.ImageField(upload_to='home-banner-images', help_text="Recommended : '1920x690'")
    social_media_url = models.URLField()
    original_resolution = '440x440'
    thumbnail_resolution = '44x44'

    def serialize(self, request=empty()):
        if USE_ORIGINAL:
            abs_img = request.build_absolute_uri(self.banner.url)
        else:
            abs_img = request.build_absolute_uri(get_thumbnail(self.banner, self.original_resolution, quality=100).url)
        tmp_img = request.build_absolute_uri(get_thumbnail(self.banner, self.thumbnail_resolution, quality=THUMB_QUALITY).url)

        return {
            'id': self.pk,
            'image': abs_img,
            'thumbnail': tmp_img,
            'slug': self.pk,
            'title': self.title,
            'range': None,
            'url': self.social_media_url
        }


class NewsLetter(models.Model):
    email = models.EmailField()

    def __str__(self):
        return self.email


class SiteConfig(SingletonModel):
    site_name = models.CharField(max_length=256, default="Grocery Store")

    sync_google_sheet_id = models.CharField(max_length=256, default="1WIeWBr4rka0SDO32VOcDw_N8tttySqC4YjC0Gh9Zr3Q")

    MIN_BASKET_AMOUNT_FOR_FREE_DELIVERY = models.PositiveSmallIntegerField(
        default=settings.MINIMUM_BASKET_AMOUNT_FOR_FREE_DELIVERY,
        help_text="MINIMUM BASKET AMOUNT FOR FREE DELIVERY")
    DELIVERY_CHARGE_FOR_FREE_DELIVERY = models.PositiveSmallIntegerField(
        default=settings.DELIVERY_CHARGE,
        help_text="DELIVERY CHARGE")
    DELIVERY_CHARGE_FOR_EXPRESS_DELIVERY = models.PositiveSmallIntegerField(
        default=settings.EXPRESS_DELIVERY_CHARGE,
        help_text="EXPRESS DELIVERY CHARGE")
    EXPECTED_OUT_FOR_DELIVERY_DELAY = models.PositiveSmallIntegerField(
        default=180,
        help_text="Expected delay between End Slot, and Delivery Boy moving out for free delivery (in minutes)!")
    EXPECTED_OUT_FOR_DELIVERY_DELAY_IN_EXPRESS_DELIVERY = models.PositiveIntegerField(
        default=180,
        help_text="Expected delay between End Slot, and Delivery Boy moving out for express delivery"
                  "(in minutes)!")
    DEFAULT_PERIOD_OF_RETURN = models.PositiveIntegerField(
        default=settings.DEFAULT_PERIOD_OF_RETURN['minutes'],
        help_text="Default Period of Return (in minutes)!")
    DEFAULT_PERIOD_OF_PICKUP = models.PositiveIntegerField(
        default=24*60,
        help_text="Default Period of Return (in minutes)!")

    referrer = 'site-config'

    home_seo_title = models.CharField(max_length=120, null=True, blank=True)
    home_seo_description = models.CharField(max_length=255, null=True, blank=True)
    home_seo_keywords = models.CharField(max_length=255, null=True, blank=True)
    home_seo_image = models.ImageField(null=True, blank=True)
    home_seo_image_alt = models.CharField(max_length=255, null=True, blank=True)
    home_seo_footer = RichTextField(null=True, blank=True)

    contact_us_emails = models.CharField(max_length=512, default="abchauzdigital@gmail.com",
                                         help_text="You can have comma seperated email to send to multiple email address.")



    @property
    def expected_out_for_delivery_delay(self):
        return timedelta(minutes=self.EXPECTED_OUT_FOR_DELIVERY_DELAY)

    @property
    def expected_out_for_delivery_delay_in_express_delivery(self):
        return timedelta(minutes=self.EXPECTED_OUT_FOR_DELIVERY_DELAY_IN_EXPRESS_DELIVERY)

    @property
    def default_period_of_return(self):
        return timedelta(minutes=self.DEFAULT_PERIOD_OF_RETURN)

    @property
    def default_period_of_pickup(self):
        return timedelta(minutes=self.DEFAULT_PERIOD_OF_PICKUP)


class Brochure(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='brochures/', null=True, blank=True)
    type = models.CharField(max_length=50, choices=(('brochure', 'Brochure'),
                                     ('catelogue', 'Catelogue')
                                     ), null=True, blank=True)

    def __str__(self):
        return self.name

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

models_list = (ReturnReason, HomePageMegaBanner, InAppFullScreenBanner,
               InAppSliderBanner, InAppBanner, TopCategory, OfferBox, SocialMediaPost)


def notify_users_on_create(sender, instance, created, **kwargs):
    if created:
        NewOfferPushNotification().send_message("You have got a new Offer", instance.title)


def clear_cache(sender, instance, **kwargs):
    from django.core.cache import cache
    cache.delete_pattern("apps.api_set_v2.views.index?zone*")


post_save.connect(clear_cache, sender=HomePageMegaBanner)
post_save.connect(clear_cache, sender=InAppBanner)

post_save.connect(notify_users_on_create, sender=HomePageMegaBanner)
post_save.connect(notify_users_on_create, sender=InAppBannerManager)
post_save.connect(notify_users_on_create, sender=InAppSliderBanner)




import re
from decimal import Decimal

from colorfield.fields import ColorField
from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F
from django.db.models.functions import Length
from django.db.models.signals import post_save
from django.db.transaction import atomic
from django.utils.safestring import mark_safe
from oscar.apps.catalogue.abstract_models import (
    AbstractProduct, AbstractCategory, AbstractProductImage,
    AbstractProductAttribute, AbstractProductRecommendation, AbstractOption, AbstractProductAttributeValue
)
from oscar.apps.catalogue.reviews.abstract_models import AbstractProductReview
from oscar.core.loading import get_model
from sorl.thumbnail import get_thumbnail

from apps.catalogue.managers import ProductManagerSelector
from apps.partner.models import StockRecord
from apps.utils import image_not_found, get_purchase_info, purchase_info_lite_as_dict, purchase_info_as_dict
from django.utils.translation import gettext_lazy as _

from lib import cache_key
from lib.cache import cache_library
from sorl.thumbnail import ImageField


class ProductAttribute(AbstractProductAttribute):
    COLOR = "color"
    TYPE_CHOICES = (
        (AbstractProductAttribute.TEXT, _("Text")),
        (AbstractProductAttribute.INTEGER, _("Integer")),
        (AbstractProductAttribute.BOOLEAN, _("True / False")),
        (AbstractProductAttribute.FLOAT, _("Float")),
        (AbstractProductAttribute.RICHTEXT, _("Rich Text")),
        (AbstractProductAttribute.DATE, _("Date")),
        (AbstractProductAttribute.DATETIME, _("Datetime")),
        (AbstractProductAttribute.OPTION, _("Option")),
        (AbstractProductAttribute.MULTI_OPTION, _("Multi Option")),
        (AbstractProductAttribute.ENTITY, _("Entity")),
        (AbstractProductAttribute.FILE, _("File")),
        (AbstractProductAttribute.IMAGE, _("Image")),
        (COLOR, _("Color")),
    )
    is_varying = models.BooleanField(_('Is Varying For Child'), default=False)
    type = models.CharField(
        choices=TYPE_CHOICES, default=TYPE_CHOICES[0][0],
        max_length=20, verbose_name=_("Type"))

    def _validate_color(self, value):
        value = value.upper()
        valid = re.search(r'^#(?:[0-9A-F]{3}){1,2}$', value)
        if not valid:
            raise ValidationError(_("Must be a hex value (like #fff or #C0C0C0)"))
        return valid

    def save_value(self, product, value, is_visible=True):   # noqa: C901 too complex
        ProductAttributeValue = get_model('catalogue', 'ProductAttributeValue')
        try:
            value_obj = product.attribute_values.get(attribute=self)
            value_obj.is_visible = is_visible
        except ProductAttributeValue.DoesNotExist:
            # FileField uses False for announcing deletion of the file
            # not creating a new value
            delete_file = self.is_file and value is False
            if value is None or value == '' or delete_file:
                return
            value_obj = ProductAttributeValue.objects.create(
                product=product, attribute=self, is_visible=is_visible)

        if self.is_file:
            self._save_file(value_obj, value)
        elif self.is_multi_option:
            self._save_multi_option(value_obj, value)
        else:
            self._save_value(value_obj, value)


class ProductAttributeValue(AbstractProductAttributeValue):
    value_color = ColorField(_('Color'), blank=True, null=True)
    is_visible = models.BooleanField(_('Is Visible in Details'), default=True)

    @property
    def _color_as_text(self):
        return self.value

    @property
    def _color_as_html(self):
        basic_styles = "height:1.75rem; width:1.75rem;border-radius:1rem;1px 1px 3px 1px #c0c0c0; display:inline-block"
        bg_color = self.value_color
        return mark_safe(f"""<span style="{basic_styles}; background-color:{bg_color}">&nbsp;</span>""")


class Brand(models.Model):
    name = models.CharField(max_length=48)

    def __str__(self):
        return str(self.name) or '-'


class FavoriteProduct(models.Model):
    product_id = models.ForeignKey('catalogue.Product', on_delete=models.CASCADE)
    user_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True, auto_created=True)


class Product(AbstractProduct):
    search = SearchVectorField(null=True)
    selected_stock_record = None

    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True)

    # just cached pricing
    effective_price = models.FloatField(_('Effective Retail Price.'), null=True, blank=True)
    retail_price = models.FloatField(_('Retail Price.'), null=True, blank=True)

    about = models.TextField(null=True, blank=True)
    storage_and_uses = models.TextField(null=True, blank=True)
    benifits = models.TextField(null=True, blank=True)
    other_product_info = models.TextField(null=True, blank=True)
    variable_weight_policy = models.TextField(null=True, blank=True)
    tax = models.SmallIntegerField(default=18, choices=[
        (5, '5% GST'),
        (12, '12% GST'),
        (18, '18% GST'),
        (28, '28% GST'),
        (0, '0% Tax'),
    ])
    is_vegetarian = models.BooleanField(default=False)
    is_meet = models.BooleanField(default=False)
    favorite = models.ManyToManyField(settings.AUTH_USER_MODEL, through=FavoriteProduct)
    weight = models.FloatField(null=True, blank=True, help_text="Weight of packed box in (kg). Used for Delivery")
    length = models.FloatField(null=True, blank=True, help_text="Length of packed box in (mm). Used for Delivery")
    width = models.FloatField(null=True, blank=True, help_text="Width of packed box in (mm). Used for Delivery")
    height = models.FloatField(null=True, blank=True, help_text="Height of packed box in (mm). Used for Delivery")
    # Product has no ratings if rating is None
    rating = models.FloatField(_('Rating'), null=True, editable=False)
    rating_count = models.IntegerField(default=0, help_text="Count of Ratings")
    review_count = models.IntegerField(default=0, help_text="Count of Reviews")

    upselling = models.ManyToManyField(
        'catalogue.Product', blank=True,
        related_name='upsell_with',
        verbose_name=_("Upselling products"),
        help_text=_("These are products that are recommended to accompany the "
                    "main product."))
    crossselling = models.ManyToManyField(
        'catalogue.Product', blank=True,
        related_name='crosssell_with',
        verbose_name=_("Cross Selling products"),
        help_text=_("These are products that are recommended to accompany the "
                    "main product."))
    browsable = ProductManagerSelector().strategy()

    def get_brand_name(self):
        instance = self
        return instance.brand.name if instance.brand else (
            (instance.parent.brand and instance.parent.brand.name) if instance.parent else None)

    def update_rating(self):
        """
        Recalculate rating field
        """
        self.rating, self.rating_count, self.review_count = self.calculate_rating()
        self.save()
    update_rating.alters_data = True

    def calculate_rating(self):
        """
        Calculate rating value
        """
        result = self.reviews.filter(
            status=self.reviews.model.APPROVED
        ).aggregate(
            sum=models.Sum('score'), count=models.Count('id'),
            review_cnt=models.Count('id', filter=models.Q(title__isnull=False)),
        )
        rating_sum = result['sum'] or 0
        rating_count = result['count'] or 0
        review_count = result['review_cnt'] or 0
        rating = None
        if rating_count > 0:
            rating = float(rating_sum) / rating_count
        return rating, rating_count, review_count

    @property
    def tax_value(self) -> Decimal:
        return Decimal(f"{self.tax / 100}")

    class Meta(AbstractProduct.Meta):
        indexes = [
            GinIndex(fields=['search']),
        ]

        app_label = 'catalogue'
        ordering = ['-date_created']
        verbose_name = _('Product')
        verbose_name_plural = _('Products')

    def _save_price(self, request=None, user=None):
        purchase_info = get_purchase_info(product=self, request=request, user=user)
        out = purchase_info_lite_as_dict(purchase_info)
        self.effective_price = out.get('effective_price')
        self.retail_price = out.get('retail')

    def categories_indexed(self):
        return [*self.categories.all().values_list('name', flat=True)]

    def get_apt_child(self, **kwargs):
        """
        if product is parent:
            calculates the product with lowest price !
            if no  product with stock available, then most reviewed product is returned!
        else same product is returned!
        """
        if self.structure in [self.STANDALONE, self.CHILD]:
            return self
        sr = StockRecord.objects.filter(product__in=self.children.all())
        if 'order' in kwargs.keys():
            sr = sr.order_by('price_excl_tax')
        sr = sr.first()
        if sr:
            return sr.product
        return self.children.filter('-rating').first()

    @property
    def name(self):
        return self.get_title()

    def __cached_primary_image_logic(self):
        img = self.primary_image()
        return img['original'] if type(img) is dict else img.thumbnail_mobile_listing

    def _set_request_context(self, request):
        self.request_context = {'request': request}

    def _recalculate_price_cache(self):
        request = getattr(self, 'request_context', {}).get('request')
        purchase_info = get_purchase_info(self, request=request)  # noqa
        if purchase_info:
            from oscarapi.serializers.product import AvailabilitySerializer
            availability = AvailabilitySerializer(purchase_info.availability).data
        else:
            availability = {
                "is_available_to_buy": False,
                "message": "Unavailable"
            }
        return purchase_info_as_dict(purchase_info, **availability)

    def _recalculate_price_cache_lite(self):
        purchase_info = get_purchase_info(self)  # noqa
        from oscarapi.serializers.product import AvailabilitySerializer
        availability = AvailabilitySerializer(purchase_info.availability).data[
            'is_available_to_buy'
        ] if purchase_info else False
        return purchase_info_lite_as_dict(purchase_info, availability=availability)

    def clear_price_caches(self):
        cache_key.product_price_data_lite__key(self.id)
        cache_key.product_price_data__key(self.id)

    def clear_list_caches(self):
        # Removing cache which loads siblings
        if self.is_parent:
            key = cache_key.parent_product_sibling_data__key(self.id)
            cache.delete(key)
            key = cache_key.product_price_data__key(self.id)
            cache.delete(key)
            key = cache_key.product_price_data_lite__key(self.id)
            cache.delete(key)
            key = cache_key.product_price_data_lite__key(self.id)
            cache.delete(key)

        # Removing all category in listing page which contains this product
        category_slugs = self.categories.all().values_list('slug')
        for category in category_slugs:
            for i in [1, 2, 3, 4]:
                c_key = cache_key.product_list__key.format(1, settings.DEFAULT_PAGE_SIZE, category)
                cache.delete(c_key)


class Category(AbstractCategory):

    image = ImageField(_('Image'), upload_to='categories', blank=True,
                       null=True, max_length=255)
    icon = ImageField(_('Icon Image'), upload_to='categories', blank=True,
                      help_text="Used to display in Homepage Icon. Suggested svg images or img less than 255X255px",
                      null=True, max_length=255)
    exclude_in_listing = models.BooleanField(default=False)

    product_class = models.ForeignKey('catalogue.ProductClass', on_delete=models.SET_NULL, null=True, blank=True)

    @property
    def thumbnail_web_listing(self):
        if self.image:
            return get_thumbnail(self.image, '500x600', crop='center', quality=98).url
        return image_not_found()

    @property
    def img_thumb_mob(self):
        if self.image:
            return get_thumbnail(self.image, '500x600', crop='center', quality=98).url
        return image_not_found()

    @property
    def icon_thumb_mob(self):
        try:
            if self.icon:
                return get_thumbnail(self.icon, '128x128', crop='center', quality=98).url
        except Exception as e:
            pass
        return image_not_found()


class ProductImage(AbstractProductImage):

    original = ImageField(_("Original"), upload_to=settings.OSCAR_IMAGE_FOLDER, max_length=255)

    @property
    def thumbnail_web_listing(self):
        if self.original:
            return get_thumbnail(self.original, '255x283', crop='center', quality=98).url
        return image_not_found()

    @property
    def thumbnail_web_desktop_thumb(self):
        if self.original:
            return get_thumbnail(self.original, '100x100', crop='center', quality=70).url
        return image_not_found()

    @property
    def thumbnail_web_desktop(self):
        if self.original:
            return get_thumbnail(self.original, '540x600', crop='center', quality=98).url
        return image_not_found()

    @property
    def thumbnail_web_zoom(self):
        if self.original:
            return get_thumbnail(self.original, '810x900', crop='center', quality=90).url
        return image_not_found()

    @property
    def thumbnail_mobile_listing(self):
        if self.original:
            return get_thumbnail(self.original, '163x178', crop='center', quality=98).url or image_not_found()
        return image_not_found()

    @property
    def thumbnail_mobile_detail(self):
        if self.original:
            return get_thumbnail(self.original, '375x360', crop='center', quality=98).url or image_not_found()
        return image_not_found()


class SearchResponses(models.Model):
    """
    Not Using. Generated to use with Autosuggestion and mappng search with a type.
    Need Population.
    """
    term = models.CharField(max_length=64)
    usage = models.IntegerField(default=1, help_text="Count of Products Which Matches this query on last calculation")
    rank = models.FloatField(default=0.0,  help_text="Ranking of term")
    hits = models.IntegerField(default=0)
    product_class = models.ForeignKey(
        'catalogue.ProductClass',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        verbose_name=_('Product type'), related_name="matching_searches",
        help_text=_("Choose what type of product this is"))

    def set_usage(self):
        from lib.product_utils import apply_search
        queryset = apply_search(queryset=Product.browsable.browsable(), search=self.term).count()

    def set_rank(self):
        raise NotImplemented()

    @atomic
    def add_hit(self):
        self.__class__.objects.filter(pk=self.pk).update(rank=F('rank')+1)  # to prevent manipulation of data
        self.refresh_from_db(fields=('rank', ))

    @classmethod
    def populate(cls):
        return cls.objects.all()


class ProductRecommendation(AbstractProductRecommendation):
    pass


class CartSpecificProductRecommendation(AbstractProductRecommendation):
    primary = models.ForeignKey(
        'basket.Basket',
        on_delete=models.CASCADE,
        related_name='primary_recommendations',
        verbose_name=_("Cart"))

    class Meta:
        app_label = 'catalogue'
        ordering = ['primary', '-ranking']
        unique_together = ('primary', 'recommendation')
        verbose_name = _('Basket Based recommendation')
        verbose_name_plural = _('Basket Based recomendations')


from oscar.apps.catalogue.models import *  # noqa isort:skip


def clear_cache_product(sender, instance, **kwargs):
    cache.delete_pattern("product_list__page:*")


def clear_cache_category(sender, instance, **kwargs):
    cache.delete_pattern("categories_list_cached")
    cache.delete_pattern("apps.api_set_v2.views.index?zone=*")


post_save.connect(clear_cache_category, sender=Category)
post_save.connect(clear_cache_product, sender=Product)


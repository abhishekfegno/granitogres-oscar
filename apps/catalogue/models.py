from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.core.cache import cache
from django.db import models
from django.db.models import F
from django.db.transaction import atomic
from oscar.apps.catalogue.abstract_models import AbstractProduct, AbstractCategory, AbstractProductImage, \
    AbstractProductAttribute
from oscar.core.loading import get_model
from sorl.thumbnail import get_thumbnail

from apps.utils import image_not_found, get_purchase_info, purchase_info_lite_as_dict, purchase_info_as_dict
from django.utils.translation import gettext_lazy as _

from lib import cache_key
from lib.cache import cache_library
from sorl.thumbnail import ImageField

StockRecord = get_model('partner', 'StockRecord')


class Product(AbstractProduct):

    additional_product_information = models.TextField(_('Description'), blank=True, null=True)
    care_instructions = models.TextField(_('Care Instructions'), blank=True, null=True)
    customer_redressal = models.TextField(_('Customer Redressal'), blank=True, null=True)
    merchant_details = models.TextField(_('Merchant Details'), blank=True, null=True)
    returns_and_cancellations = models.TextField(_('Returns & Cancellations'), blank=True, null=True)
    warranty_and_installation = models.TextField(_('Warranty & Installation'), blank=True, null=True)
    # documents = models.FileField(_('Documents'), blank=True, null=True)

    shipping_charge = models.FloatField(_('Shipping Charge'), blank=True, null=True)
    search = SearchVectorField(null=True)

    # just cached pricing
    effective_price = models.FloatField(_('Effective Retail Price.'), null=True, blank=True)
    retail_price = models.FloatField(_('Retail Price.'), null=True, blank=True)

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

        # Removing all category in listing page which contains this product
        category_slugs = self.categories.all().values_list('slug')
        for category in category_slugs:
            for i in [1, 2, 3, 4]:
                c_key = cache_key.product_list__key.format(1, settings.DEFAULT_PAGE_SIZE, category)
                cache.delete(c_key)


class Category(AbstractCategory):

    image = ImageField(_('Image'), upload_to='categories', blank=True,
                       null=True, max_length=255)

    @property
    def thumbnail_web_listing(self):
        if self.image:
            return get_thumbnail(self.image, '500x600', crop='center', quality=98).url
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
            return get_thumbnail(self.original, '163x178', crop='center', quality=98).url
        return image_not_found()

    @property
    def thumbnail_mobile_detail(self):
        if self.original:
            return get_thumbnail(self.original, '375x360', crop='center', quality=98).url
        return image_not_found()


class ProductAttribute(AbstractProductAttribute):
    is_varying = models.BooleanField(_('Is Varying For Child'), default=False)


from oscar.apps.catalogue.models import *  # noqa isort:skip


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
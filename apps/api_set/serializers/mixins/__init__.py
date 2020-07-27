from django.core.cache import cache
from django.db.models import F
from oscar.apps.catalogue.abstract_models import MissingProductImage
from oscar.core.loading import get_model
from oscarapi.utils.loading import get_api_class

from apps.catalogue.models import ProductImage
from apps.utils import get_purchase_info, purchase_info_as_dict, purchase_info_lite_as_dict, image_not_found, \
    dummy_purchase_info_lite_as_dict
from lib import cache_key
from lib.algorithms.product import siblings_pointer
from lib.cache import cache_library, get_featured_path


Product = get_model("catalogue", "Product")
Category = get_model("catalogue", "Category")
ProductClass = get_model("catalogue", "ProductClass")
CategoryField = get_api_class("serializers.fields", "CategoryField")
ProductAttributeValueSerializer = get_api_class('serializers.product', 'ProductAttributeValueSerializer')
OptionSerializer = get_api_class('serializers.product', 'OptionSerializer')
AvailabilitySerializer = get_api_class('serializers.product', 'AvailabilitySerializer')


class ProductPrimaryImageFieldMixin(object):

    def get_primary_image(self, instance):
        req = self.context['request'] # noqa: mixin assured
        img = instance.primary_image()
        img_mob = img['original'] if type(img) is dict else img.thumbnail_mobile_listing
        return {
            # 'web': req.build_absolute_uri(img_web),
            'mobile': req.build_absolute_uri(img_mob or image_not_found()),
        }


class ProductAttributeFieldMixin(object):
    attribute_values_filter = {}

    def get_attributes(self, instance):
        def _inner():
            """
             Executing 5 Queries!
            """
            # import pdb; pdb.set_trace()
            attrs_value = instance.attribute_values.filter(
                **self.attribute_values_filter
            ).annotate(
                att_name=F('attribute__name'),
                att_code=F('attribute__code'),
            )
            return [{       # saves model mapping and another 5 queries
                'name': attr.att_name,
                'value': attr.value_as_text,
                'code': attr.att_code,
            } for attr in attrs_value]
        cache.delete(cache_key.product_attribute__key(instance.id))
        return cache_library(cache_key.product_attribute__key(instance.id), cb=_inner)


class SibblingProductAttributeFieldMixin(ProductAttributeFieldMixin):
    # attribute_values_filter = {'attribute__is_varying': True}
    pass


class ProductPriceFieldMixin(object):

    def get_price(self, product):
        request = (self.context or {}).get('request')
        purchase_info = get_purchase_info(product, request)  # noqa
        if purchase_info:
            from oscarapi.serializers.product import AvailabilitySerializer
            availability = AvailabilitySerializer(purchase_info.availability).data
        else:
            availability = {
                "is_available_to_buy": False,
                "message": "Unavailable"
            }
        return purchase_info_as_dict(purchase_info, **availability)


        # cache.delete(cache_key.product_price_data__key(product.id))
        # return cache_library(
        #     cache_key.product_price_data__key(product.id),
        #     cb=product._recalculate_price_cache
        # )


class ProductPriceFieldMixinLite(object):

    def get_price(self, product):
        key = 'ProductPriceFieldMixinLite__{0}__{1}'

        def _inner():
            if product.is_parent:
                return dummy_purchase_info_lite_as_dict(availability=False, availability_message='')
            purchase_info = get_purchase_info(product, request=self.context['request'])  # noqa
            addittional_informations = {
                "availability": bool(purchase_info.availability.is_available_to_buy),
                "availability_message": purchase_info.availability.short_message,
            }
            return purchase_info_lite_as_dict(purchase_info, **addittional_informations)

        return _inner()


class ProductDetailSerializerMixin(object):

    def get_name(self, instance):
        return self.context['product'].get_title()

    def get_description(self, instance):
        # return striptags(self.context['product'].description)
        return self.context['product'].description

    def get_categories(self, instance):
        featured = get_featured_path()
        return instance.get_categories().exclude(slug__startswith=featured).values_list('name', flat=True)

    def get_recommended_products(self, instance):
        inst = instance.parent if instance.is_child else instance
        from apps.api_set.serializers.catalogue import ProductSimpleListSerializer
        return ProductSimpleListSerializer(
            inst.sorted_recommended_products,
            many=True,
            context=self.context
        ).data

    def get_images(self, instance):
        images = instance.get_all_images()
        b = self.context['request'].build_absolute_uri
        return [
            {
                'web_desktop': b(img.thumbnail_web_desktop),
                'web_zoom': b(img.thumbnail_web_zoom),
                'mobile': b(img.thumbnail_mobile_detail),
            } for img in images
        ]

    def get_siblings(self, instance):
        if instance.is_child:
            return siblings_pointer(instance.parent, request=self.context['request'])
        if instance.is_parent:
            return siblings_pointer(instance, request=self.context['request'])
        return None


# 890 204



from django.db.models import F

from apps.dashboard.custom.models import empty
from apps.utils import image_not_found, purchase_info_as_dict, dummy_purchase_info_lite_as_dict, \
    purchase_info_lite_as_dict, get_purchase_info
from lib import cache_key
from lib.cache import cache_library


class ProductPrimaryImageFieldMixin(object):

    def get_primary_image(self, instance):
        request = (self.context or {}).get('request', empty())  # noqa: mixin assured
        req = request.build_absolute_uri
        # if instance.is_child:
        #     return {
        #         'mobile': req(image_not_found()),
        #     }
        img = instance.primary_image()
        org_url = image_not_found() if type(img) is dict else getattr(img.original, 'url')
        img_mob = image_not_found() if type(img) is dict else img.thumbnail_mobile_listing
        return {
            'web': org_url and req(org_url),
            'mobile': req(img_mob),
        }


class ProductAttributeFieldMixin(object):
    attribute_values_filter = {}

    def get_attributes(self, instance):
        def _inner():
            """
             Executing 5 Queries!
            """
            attrs_value = instance.attribute_values.filter(
                **self.attribute_values_filter
            ).filter(attribute__is_visible_in_detail_page=True).annotate(
                att_name=F('attribute__name'),
                att_code=F('attribute__code'),
            ).order_by('attribute__order_in_detail_page')
            return [{       # saves model mapping and another 5 queries
                'name': attr.att_name,
                'value': attr.value_as_text,
                'code': attr.att_code,
            } for attr in attrs_value]
        return _inner()


class SibblingProductAttributeFieldMixin(ProductAttributeFieldMixin):
    # attribute_values_filter = {'attribute__is_varying': True}
    pass


class ProductPriceFieldMixin(object):

    def get_price(self, product):
        if product.is_parent:
            return
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
        def _inner():
            if product.is_parent:
                return dummy_purchase_info_lite_as_dict(availability=True, availability_message='')
            purchase_info = get_purchase_info(
                product,
                request=self.context['request']     # noqa: mixin ensures
            )
            addittional_informations = {
                "availability": bool(purchase_info.availability.is_available_to_buy),
                "availability_message": purchase_info.availability.short_message,
            }
            return purchase_info_lite_as_dict(purchase_info, **addittional_informations)

        return _inner()

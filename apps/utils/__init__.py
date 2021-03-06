from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.encoding import force_text
from django.utils.functional import Promise
import math
from apps.partner.strategy import Selector
from lib.currencies import get_symbol
from lib.utils import get_approximate_tax_for_retail


def image_not_found(request=None):
    b = request.build_absolute_uri if request else lambda x: x
    return b(
        "{}{}".format(
            settings.STATIC_URL,
            settings.OSCAR_MISSING_IMAGE_URL
        )
    )


def banner_not_found(request=None):
    b = request.build_absolute_uri if request else lambda x: x
    return b(
        "{}{}".format(
            settings.STATIC_URL,
            settings.MISSING_BANNER_URL
        )
    )


def get_purchase_info(product, request=None, user=None):

    strategy = Selector().strategy(request, user)
    if product.is_parent:
        return strategy.fetch_for_parent(product=product)
    else:
        return strategy.fetch_for_product(product=product)


def purchase_info_as_dict(purchase_info, **kwargs):
    if not purchase_info or not purchase_info.stockrecord:
        return {}
    retail_rate = hasattr(purchase_info.stockrecord, 'price_retail') and purchase_info.stockrecord.price_retail or None
    if retail_rate:
        retail_rate = get_approximate_tax_for_retail(
            purchase_info.price.incl_tax,
            purchase_info.price.excl_tax,
            retail_rate
        )
    return {
        'stockrecord': hasattr(purchase_info.stockrecord, 'id') and purchase_info.stockrecord.id or None,
        'partner_id': hasattr(purchase_info.stockrecord, 'partner_id') and purchase_info.stockrecord.partner_id or None,
        'partner_sku': hasattr(purchase_info.stockrecord, 'partner_sku') and purchase_info.stockrecord.partner_sku or None,
        'low_stock': purchase_info.stockrecord and purchase_info.stockrecord.low_stock_threshold and purchase_info.stockrecord.net_stock_level <= purchase_info.stockrecord.low_stock_threshold,
        'net_stock_level': purchase_info.stockrecord and max(purchase_info.stockrecord.net_stock_level or 0, 0),
        'effective_price': purchase_info.price.effective_price,
        'currency': purchase_info.price.currency,
        'symbol': get_symbol(purchase_info.price.currency),
        'excl_tax': purchase_info.price.excl_tax,
        'incl_tax': purchase_info.price.incl_tax,
        'is_tax_known': purchase_info.price.is_tax_known,
        'retail': retail_rate,
        'tax': purchase_info.price.tax,
        'availability': {**kwargs} if kwargs.keys() else None
    }


def purchase_info_lite_as_dict(purchase_info, **kwargs):
    if not purchase_info or not purchase_info.stockrecord:
        return dummy_purchase_info_lite_as_dict(**kwargs)
    try:
        retail_rate = hasattr(purchase_info.stockrecord, 'price_retail') and purchase_info.stockrecord.price_retail or None
        low_stock = False
        net_stock_level = 0
        sr = purchase_info.stockrecord
        if sr and sr.low_stock_threshold:
            low_stock = sr.net_stock_level <= sr.low_stock_threshold
        if sr:
            net_stock_level = max(sr.net_stock_level or 0, 0)
        if net_stock_level == 0:
            low_stock = False
        return {
            'excl_tax': purchase_info.price.effective_price,
            'effective_price': purchase_info.price.effective_price,
            'retail': int(retail_rate * 100) / 100,
            'low_stock': low_stock,
            'net_stock_level': net_stock_level,
            'currency': purchase_info.price.currency,
            'symbol': get_symbol(purchase_info.price.currency),
            **kwargs
        }
    except Exception as e:
        return dummy_purchase_info_lite_as_dict(**kwargs)


def dummy_purchase_info_lite_as_dict(**kwargs):
    return {
        'excl_tax': 0,
        'effective_price': 0,
        'retail': 0,
        'low_stock': False,
        'net_stock_level': 0,
        'currency': 'INR',
        'symbol': get_symbol('INR'),
        **kwargs
    }


class LazyEncoder(DjangoJSONEncoder):

    def default(self, obj):
        if isinstance(obj, Promise):
            return force_text(obj)
        else:
            return super(LazyEncoder, self).default(obj)




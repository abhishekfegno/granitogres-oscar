from typing import Any, Union

from django.db.models import Q, QuerySet, Case, Value, When, IntegerField
from django.http import HttpRequest

from apps.api_set_v2.serializers.catalogue import ProductSimpleListSerializer
from apps.availability.models import Zones
from apps.catalogue.models import Product
from apps.partner.models import StockRecord


def get_optimized_product_dict(
        request: HttpRequest,
        qs_filter: Q = None,
        qs: Union[QuerySet, list] = None,
        offset: int = None,
        limit: int = None,
        needs_stock: bool = False,
        product_serializer_class: type = ProductSimpleListSerializer) -> dict:

    assert qs is not None or qs_filter is not None, "Either one is required!"
    """
    Zone can be explained as a model with a pointer to partner who delivers to a geographical region.
    zone:  = None 

    class Zone(models.Model):
        name = models.CharField(max_length=128)
        zone = models.PolygonField()
        partner = models.ForeignKey('partner.Partner', related_name='zone', on_delete=models.CASCADE)

    stock record -> partner -> zone
    
    """
    zone = None
    if request.GET.get('pincode'):
        from apps.availability.facade import ZoneFacade, get_zone_from_pincode
        _zone = get_zone_from_pincode(request.GET.get('pincode'))
        zone = _zone.id
    if zone is None:
        zone: int = request.session.get('zone')         # zone => Zone.pk
    if qs is not None:
        if not qs:
            return {}
        product_set = qs
        # product_set = Product.objects.filter(id__in=qs.values_list('id', flat=True))

    else:
        product_set = Product.objects.filter(
            qs_filter, is_public=True,
            # stockrecords__isnull=False
        )
    # if needs_stock:
    #     product_set = product_set.filter(stockrecords__isnull=False)
    # if offset and limit:
    #     product_set = product_set[offset:limit]
    # elif limit:
    #     product_set = product_set[:limit]
    # elif offset:
    #     product_set = product_set[offset:]

    st_set_01 = StockRecord.objects.filter(
        product__in=product_set, product__structure=Product.STANDALONE).values_list('id')
    st_set_02 = StockRecord.objects.filter(
        product__in=Product.objects.filter(parent__in=product_set),
        product__structure=Product.CHILD).values_list('id')

    sr_set = StockRecord.objects.filter(
        id__in=(st_set_01 | st_set_02),
        product__structure__in=[Product.CHILD, Product.STANDALONE],
        num_in_stock__gte=1 if needs_stock else 0,
    ).annotate(to_first=Case(
        When(num_in_stock=0, then=Value(0)), default=Value(1), output_field=IntegerField()
    )).select_related(
        'product', 'product__product_class', 'product__parent', 'product__parent__product_class'
    ).prefetch_related('product__images', 'product__parent__images').order_by('to_first')
    _zones = []
    if zone:
        _zones = Zones.objects.filter(pk=zone).values_list('partner_id', flat=True)
    else:
        _zones = Zones.objects.order_by('-is_default_zone').values_list('partner_id', flat=True)
    sr_set = sr_set.filter(partner_id__in=_zones)

    if offset and limit:
        sr_set = sr_set[offset:limit]
    elif limit:
        sr_set = sr_set[:limit]
    elif offset:
        sr_set = sr_set[offset:]

    product_data = {}
    cxt = {'request': request}
    for sr in sr_set[:limit]:
        sr.product.selected_stock_record = sr
        if sr.product.is_child:
            if sr.product.parent not in product_data.keys():
                product_data[sr.product.parent] = product_serializer_class(instance=sr.product.parent, context={**cxt}).data
                product_data[sr.product.parent]['variants'] = []
            product_data[sr.product.parent]['variants'].append(
                product_serializer_class(instance=sr.product, context={'request': request}).data)
        elif sr.product.is_standalone:  # parent or standalone
            product_data[sr.product] = product_serializer_class(instance=sr.product, context=cxt).data
            product_data[sr.product]['variants'] = []
    # if not needs_stock:
    #     for product in product_set:
    #         if product.is_child:
    #             if product.parent not in product_data:
    #                 if product.parent not in product_data.keys():
    #                     product_data[product.parent] = product_serializer_class(
    #                                                                         instance=product.parent, context=cxt).data
    #                     product_data[product.parent]['variants'] = []
    #                 product_data[product.parent]['variants'].append(
    #                     product_serializer_class(instance=product, context=cxt).data)
    #         elif product.is_standalone:  # parent or standalone
    #             if product not in product_data:
    #                 product_data[product] = product_serializer_class(instance=product, context=cxt).data
    #                 product_data[product]['variants'] = []
    return product_data


def get_optimized_product_dict_for_child(
        request: HttpRequest,
        qs_filter: Q = None,
        qs: Union[QuerySet, list] = None,
        offset: int = None,
        limit: int = None,
        needs_stock: bool = False,
        product_serializer_class: type = ProductSimpleListSerializer) -> dict:
    assert qs is not None or qs_filter is not None, "Either one is required!"
    """
    Zone can be explained as a model with a pointer to partner who delivers to a geographical region.
    zone:  = None 

    class Zone(models.Model):
        name = models.CharField(max_length=128)
        zone = models.PolygonField()
        partner = models.ForeignKey('partner.Partner', related_name='zone', on_delete=models.CASCADE)

    stock record -> partner -> zone

    """
    zone: int = request.session.get('zone')  # zone => Zone.pk
    if qs is not None:
        if not qs:
            return {}
        product_set = qs
        # product_set = Product.objects.filter(id__in=qs.values_list('id', flat=True))

    else:
        product_set = Product.objects.filter(
            qs_filter, is_public=True,
            # stockrecords__isnull=False
        )
    # if needs_stock:
    #     product_set = product_set.filter(stockrecords__isnull=False)
    if offset and limit:
        product_set = product_set[offset:limit]
    elif limit:
        product_set = product_set[:limit]
    elif offset:
        product_set = product_set[offset:]

    st_set_01 = StockRecord.objects.filter(product__in=product_set).values_list('id')

    sr_set = StockRecord.objects.filter(
        id__in=st_set_01,
        product__structure__in=[Product.CHILD, Product.STANDALONE],
        num_in_stock__gte=1 if needs_stock else 0,
    ).annotate(to_first=Case(
        When(num_in_stock=0, then=Value(0)), default=Value(1), output_field=IntegerField()
    )).select_related(
        'product', 'product__product_class', 'product__parent', 'product__parent__product_class'
    ).prefetch_related('product__images', 'product__parent__images').order_by('to_first')
    if zone:
        sr_set = sr_set.filter(partner__zone__id=zone)

    # if offset and limit:
    #     sr_set = sr_set[offset:limit]
    # elif limit:
    #     sr_set = sr_set[:limit]
    # elif offset:
    #     sr_set = sr_set[offset:]

    product_data = {}
    cxt = {'request': request}
    for sr in sr_set[:limit]:
        sr.product.selected_stock_record = sr
        if sr.product.is_child:
            if sr.product.parent not in product_data.keys():
                product_data[sr.product.parent] = product_serializer_class(instance=sr.product.parent, context=cxt).data
                product_data[sr.product.parent]['variants'] = []
            product_data[sr.product.parent]['variants'].append(
                product_serializer_class(instance=sr.product, context={'request': request}).data)
        elif sr.product.is_standalone:  # parent or standalone
            product_data[sr.product] = product_serializer_class(instance=sr.product, context=cxt).data
            product_data[sr.product]['variants'] = []
    if not needs_stock:
        for product in product_set:
            if product.is_child:
                if product.parent not in product_data:
                    if product.parent not in product_data.keys():
                        product_data[product.parent] = product_serializer_class(
                            instance=product.parent, context=cxt).data
                        product_data[product.parent]['variants'] = []
                    product_data[product.parent]['variants'].append(
                        product_serializer_class(instance=product, context=cxt).data)
            elif product.is_standalone:  # parent or standalone
                if product not in product_data:
                    product_data[product] = product_serializer_class(instance=product, context=cxt).data
                    product_data[product]['variants'] = []
    return product_data


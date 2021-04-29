from typing import Any, Union

from django.db.models import Q, QuerySet, Case, Value, When, IntegerField
from django.http import HttpRequest

from apps.api_set_v2.serializers.catalogue import ProductSimpleListSerializer
from apps.catalogue.models import Product
from apps.partner.models import StockRecord


def get_optimized_product_dict(
        request: HttpRequest,
        qs_filter: Q = None,
        qs: Union[QuerySet, list] = None,
        offset: int = None,
        limit: int = None,
        needs_stock: bool = True,
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
    zone: int = request.session.get('zone')         # zone => Zone.pk
    if qs is not None:
        if not qs: return {}
        product_set = qs
    else:
        product_set = Product.objects.filter(
            qs_filter, is_public=True,
            # stockrecords__isnull=False
        )
    sr_set = StockRecord.objects.filter(
        Q(Q(product__parent__in=product_set)|Q(product__in=product_set)),
        product__structure__in=[Product.CHILD, Product.STANDALONE],
        num_in_stock__gt=0 if needs_stock else -1,
    ).annotate(to_first=Case(
        When(num_in_stock=0, then=Value(0)), default=Value(1), output_field=IntegerField()
    )).select_related(
        'product', 'product__product_class', 'product__parent', 'product__parent__product_class'
    ).prefetch_related('product__images', 'product__parent__images').order_by('to_first')
    if zone:
        sr_set = sr_set.filter(partner__zone__id=zone)

    # import pdb; pdb.set_trace()
    # if offset and limit:
    #     sr_set = sr_set[offset:limit]
    # elif limit:
    #     sr_set = sr_set[:limit]
    # elif offset:
    #     sr_set = sr_set[offset:]

    product_data = {}
    for sr in sr_set:
        sr.product.selected_stock_record = sr
        if sr.product.is_child:
            if sr.product.parent not in product_data.keys():
                product_data[sr.product.parent] = product_serializer_class(instance=sr.product.parent,
                                                                           context={'request': request}).data
                product_data[sr.product.parent]['variants'] = []
            product_data[sr.product.parent]['variants'].append(
                product_serializer_class(instance=sr.product, context={'request': request}).data)
        elif sr.product.is_standalone:  # parent or standalone
            product_data[sr.product] = product_serializer_class(instance=sr.product,
                                                                context={'request': request}).data
            product_data[sr.product]['variants'] = []
        if not product_data.keys() and len(product_data.keys() or []) >= limit:
            break
    return product_data









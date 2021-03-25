from pprint import pprint

from django.db.models import Q
from rest_framework.decorators import api_view
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.reverse import reverse

from apps.api_set_v2.serializers.catalogue import ProductDetailWebSerializer
from apps.api_set_v2.serializers.mixins import ProductPrimaryImageFieldMixin
from apps.api_set_v2.utils.product import get_optimized_product_dict
from apps.catalogue.models import Product

# API_V2


@api_view()
def product_detail_web(request, product: Product): # needs parent product
    queryset = Product.browsable.all().select_related('parent')
    serializer_class = ProductDetailWebSerializer       # v2
    product = get_object_or_404(queryset, pk=product)
    if product.is_child:
        product = product.parent
    img_mixin = ProductPrimaryImageFieldMixin()
    price_mixin = ProductPrimaryImageFieldMixin()
    img_mixin.context = {'request': request}
    price_mixin.context = {'request': request}
    response = get_optimized_product_dict(
        request=request,
        qs=[product, ],
    ).values()
    sol = product.sorted_recommended_products
    for r in response:
        response = r
        break
    response = {
        **response,
        "url": reverse('product-detail', request=request, kwargs={'pk': product.id}),
        "description": product.description,
        "recommended_products": [a for a in get_optimized_product_dict(
            request=request,
            qs=sol,
        ).values()],
    }

    if request.session.get('location'):
        out = {
            'message': None,
            'status': True,
        }
    else:
        out = {
            'message': 'Current Location is not provided.',
            'status': False
        }

    return Response({
        'results': response,
        'deliverable': out
    })
from django.core.cache import cache
from rest_framework.decorators import api_view
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from apps.api_set.views.orders import _login_required
from apps.api_set_v2.serializers.catalogue import ProductDetailWebSerializer
from apps.catalogue.models import Product

# API_V2
from apps.utils import image_not_found


@api_view()
@_login_required
def mark_as_fav(request, product: Product):     # needs parent product
    queryset = Product.browsable.all().select_related('parent', ).prefetch_related('images', 'parent__images')
    product = get_object_or_404(queryset, pk=product)
    status = ""
    if product.favorite.all().filter(id=request.user.id).exists():
        product.favorite.remove(request.user)
        status = "removed"
    else:
        product.favorite.add(request.user)
        status = "added"
    return Response({'status': status})


@api_view()
def product_detail_web(request, product):
    # cache.clear()
    key = f"product_detail::{product}"
    data = cache.get(key)
    if not data:
        queryset = Product.objects.base_queryset()
        serializer_class = ProductDetailWebSerializer
        product = get_object_or_404(queryset, pk=product)
        if product.is_parent:
            focused_product = product.get_apt_child(order='-price_excl_tax')
        elif product.is_child:
            focused_product = product
            product = product.parent
        else:
            focused_product = product
        data = serializer_class(instance=focused_product, context={'request': request, 'product': product}).data
        cache.set(key, data)
    if request.session.get('location'):
        out = {
            'message': None,
            'status': True,
            'data': {
                'location': {
                    "zone_id": request.session.get('zone'),
                    "zone_name": request.session.get('zone_name'),
                    "location_id": request.session.get('location'),
                    "location_name": request.session.get('location_name')
                }
            }
        }
    else:
        out = {
            'message': 'Current Location is not provided.',
            'status': False
        }

    return Response({
        'results': data,
        'deliverable': out
    })

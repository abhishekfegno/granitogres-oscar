from oscar.apps.wishlists.models import WishList
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from oscar.apps.customer.wishlists.views import WishListAddProduct

from apps.api_set.serializers.wishlist import WishListSerializer
from apps.catalogue.models import Product


def get_or_create_wishlist(request, *args, **kwargs):
    if 'key' in kwargs:
        wishlist = get_object_or_404(
            WishList, key=kwargs['key'], owner=request.user)
    else:
        wishlists = request.user.wishlists.filter(name='Default')[:1]
        if not wishlists:
            return request.user.wishlists.create()
        wishlist = wishlists[0]

    if not wishlist.is_allowed_to_edit(request.user):
        raise PermissionDenied
    return wishlist


@api_view(['GET', 'POST', 'PATCH', 'DELETE'])
def wish_list(request, **kwargs):
    """
    request : method GET, POST, PATCH, DELETE

    Usage : 01 - Get Wish List
    Method: GET
    required field : []

    Usage : 02 - Create Item.
    Method: POST
    required field : ['product_id', ]
    responses : 400  ; if product_id not available,
                404  ; if product does not exists,
                200  ; if okey

    Usage : 03 - Delete Item.
    Method: PATCH
    required field : ['product_id', ]
    responses : 400  ; if product_id not available,
                404  ; if product does not exists,
                200  ; if okey

    Usage : 04 - Clear Wish List.
    Method: DELETE
    required field : []
    responses : 400  ; if product_id not available,
                404  ; if product does not exists,
                200  ; if okey

    """
    serializer_class = WishListSerializer
    wish_list = get_or_create_wishlist(request, **kwargs)
    data = request.data

    if request.method == 'GET':
        ser = serializer_class(instance=wish_list, context={"request": request})
        return Response(ser.data)
    elif request.method == 'POST':
        if 'product_id' not in data.keys():
            return Response({'error': 'product_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        product = get_object_or_404(Product, pk=data['product_id'])
        if product.structure == Product.PARENT:
            return product.children.all().last
            # return Response({'error': 'Cannot add parent product to wishlist.'}, status=status.HTTP_400_BAD_REQUEST)
        wish_list.add(product)
    elif request.method == 'PATCH':
        if 'product_id' not in data.keys():
            return Response({'error': 'product_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            """
            Remove Product from Line.
            """
            wish_list.lines.filter(product_id=data['product_id']).delete()
    elif request.method == 'DELETE':
        wish_list.lines.all().delete()
    else:
        return Response(400)
    ser = serializer_class(instance=wish_list, context={"request": request})
    return Response(ser.data)









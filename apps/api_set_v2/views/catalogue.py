from django.core.cache import cache
from django.db import IntegrityError
from django.db.models import Prefetch
from django.http import Http404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.generics import get_object_or_404, CreateAPIView, ListAPIView, UpdateAPIView, DestroyAPIView, \
    RetrieveUpdateAPIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response

from apps.api_set.views.orders import _login_required
from apps.api_set_v2.serializers.catalogue import ProductDetailWebSerializer, ProductReviewListSerializer, \
    ProductReviewCreateSerializer, ProductReviewImageSerializer
from apps.catalogue.models import Product
# from apps.catalogue.models import ProductReview
from apps.catalogue.reviews.models import ProductReview, ProductReviewImage, Vote


# API_V2


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
    # key = f"product_detail::{product}"
    # data = cache.get(key)
    # if not data:
    queryset = Product.objects.base_queryset().prefetch_related(
        Prefetch('reviews')
    )
    serializer_class = ProductDetailWebSerializer
    # product = get_object_or_404(queryset, pk=product)
    try:
        product = queryset.get(pk=product)
    except queryset.model.DoesNotExist:
        return Response({
            "response": "Product Doesn't exist."
        }, status=status.HTTP_404_NOT_FOUND)

    if product.is_parent:
        focused_product = product.get_apt_child(order='-price_excl_tax')
    elif product.is_child:
        focused_product = product
        product = product.parent
    else:
        focused_product = product
    data = serializer_class(instance=focused_product, context={'request': request, 'product': product}).data
    # cache.set(key, data)
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


class ProductReviewListView(ListAPIView):
    serializer_class = ProductReviewListSerializer

    def get_queryset(self):
        return ProductReview.objects.filter(product_id=self.kwargs['product']).prefetch_related('images')


class ProductReviewCreateView(CreateAPIView):
    serializer_class = ProductReviewCreateSerializer
    queryset = ProductReview.objects.all()
    parser_classes = [JSONParser, MultiPartParser, FormParser, ]
    
    def post(self, request, *args, **kwargs):
        # import pdb; pdb.set_trace()
        return super(ProductReviewCreateView, self).post(request, *args, **kwargs)


class ProductReviewUpdateView(RetrieveUpdateAPIView):
    serializer_class = ProductReviewCreateSerializer
    queryset = ProductReview.objects.all()
    lookup_url_kwarg = 'review_pk'
    parser_classes = [JSONParser, MultiPartParser, FormParser, ]

    # def check_object_permissions(self, request, obj):
    #     if request.user.is_anonymous or obj.user != request.user:
    #         self.permission_denied(
    #             request, message="You do not have permission to update this review.!"
    #         )

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}
        return Response(serializer.data)


class ProductReviewDeleteView(DestroyAPIView):
    serializer_class = ProductReviewCreateSerializer
    queryset = ProductReview.objects.all()
    lookup_url_kwarg = 'review_pk'

    def check_object_permissions(self, request, obj):
        if request.user.is_anonymous or obj.user != request.user:
            self.permission_denied(
                request, message="You do not have permission to update this review.!"
            )


class ProductReviewImageDeleteView(DestroyAPIView):
    serializer_class = ProductReviewImageSerializer
    queryset = ProductReviewImage.objects.all()
    lookup_url_kwarg = 'image_id'

    def check_object_permissions(self, request, obj):
        if not obj.review:
            return
        if request.user.is_anonymous or obj.review.user != request.user:
            self.permission_denied(
                request, message="You do not have permission to update this review.!"
            )


@api_view()
def vote_review(request, review_pk):
    review = get_object_or_404(ProductReview, pk=review_pk)

    stat, reason = review.can_user_vote(request.user)
    if stat is False:
        return Response({
            'response': reason
        }, status.HTTP_401_UNAUTHORIZED)
    Vote.objects.filter(review=review, user=request.user).delete()
    reason = ""
    if request.data.get('vote') == 'down':
        review.vote_down(request.user)
        reason = "Down Voted!"
    else:
        review.vote_up(request.user)
        reason = "Up Voted!"
    return Response({
        'status': 'success',
        'response': reason
    }, status.HTTP_200_OK)



from allauth.account.models import EmailAddress
from django.conf import settings
from django.core.paginator import Paginator
from django.db import models
from django.utils.timezone import now
from oscar.apps.offer.models import ConditionalOffer
from oscar.core.loading import get_model
from oscarapi.utils.loading import get_api_class, get_api_classes
from rest_framework.decorators import api_view
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from apps.api_set.serializers.catalogue import (
    CategorySerializer, Category, Product,
    ProductListSerializer, SimpleOfferBannerSerializer
)
from apps.basket.models import Basket
from apps.dashboard.custom.models import OfferBanner
from apps.utils.urls import list_api_formatter
from lib.cache import get_featured_path


BasketSerializer = get_api_class("serializers.basket", "BasketSerializer")
Order = get_model('order', 'Order')
BasketLine = get_model('basket', 'Line')


@api_view(("GET",))
def home(request, *a, **k):
    user = None
    b_count = 0
    profile = None
    if request.user.is_authenticated:
        user_fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_active', ]
        user = {field: getattr(request.user, field) for field in user_fields}
        request.session['is_email_verified'] = request.session.get(
            'is_email_verified', False) or EmailAddress.objects.filter(user=request.user, verified=True).exists()

        request.session['has_address'] = request.session.get('has_address', False) or request.user.addresses.all().exists()
        b_count = Basket.open.filter(owner=request.user).last().num_lines
        profile = {
            'mobile': request.user._profile.mobile,
            'gst_number': request.user._profile.gst_number,
            'pincode': request.user._profile.pincode and request.user._profile.pincode.code,
        }

    else:
        request.session['has_address'] = None
        request.session['is_email_verified'] = None

    return Response({
        "user": user,
        "profile":  profile,
        "user_email_verified": request.session['is_email_verified'],
        "cart_item_count": b_count,
        "user_has_address":  request.session['has_address'],
    })


@api_view(("GET",))
def index(request, *a, **k):
    cxt = {'context': {'request': request}}

    return Response({
        "featured_collections": CategorySerializer(
            Category.objects.filter(path__startswith=get_featured_path(), depth=2),
            **cxt,
            many=True).data,
        "new_arrivals": ProductListSerializer(
            Product.objects.filter(id__in=Product.browsable.browsable().values_list('id', flat=True))[:8],
            many=True,
            **cxt).data,
    })


@api_view(("GET",))
def offers(request, *a, **k):
    cxt = {'context': {'request': request}}
    cutoff = now()
    offers = OfferBanner.objects.all().filter(
        offer__status=ConditionalOffer.OPEN
    ).filter(
        models.Q(offer__end_datetime__gte=cutoff) | models.Q(offer__end_datetime=None),
        models.Q(offer__start_datetime__lte=cutoff) | models.Q(offer__start_datetime=None)
    ).order_by('order', '-id')

    return Response({
        "offer_list": SimpleOfferBannerSerializer(
            offers,
            **cxt,
            many=True).data,
    })


@api_view(("GET",))
def offer_products(request, *a, **k):
    cxt = {'context': {'request': request}}

    serializer_class = ProductListSerializer
    page_number = request.GET.get('page', 1)
    page_size = request.GET.get('page_size', settings.DEFAULT_PAGE_SIZE)

    obj = get_object_or_404(OfferBanner, code=k.get('slug'), offer__status=ConditionalOffer.OPEN)
    queryset = obj.products().filter(
        structure__in=['standalone', 'child'], is_public=True, stockrecords__isnull=False
    ).distinct('id').order('-id')
    paginator = Paginator(queryset, page_size)  # Show 18 contacts per page.
    page_obj = paginator.get_page(page_number)
    product_data = serializer_class(page_obj.object_list, many=True, context={'request': request}).data

    return Response(list_api_formatter(request, page_obj=page_obj, results=product_data))


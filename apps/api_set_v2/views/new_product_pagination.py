from django.conf import settings
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q
from oscar.apps.basket.utils import ConditionalOffer
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.response import Response

from apps.api_set_v2.serializers.catalogue import ProductSimpleListSerializer
from apps.api_set_v2.utils.product import get_optimized_product_dict
from apps.api_set_v2.views.product_listing_query_pagination import get_breadcrumb
from django.utils.translation import ugettext as _

from apps.availability.models import Zones
from apps.catalogue.models import Product, ProductClass
from apps.dashboard.custom.models import OfferBanner
from apps.dashboard.ranges.models import Range
from apps.partner.models import StockRecord
from apps.utils.urls import list_api_formatter
from lib.product_utils import category_filter, recommended_class, apply_filter, apply_search, apply_sort

# sorting
RELEVANCY = "relevancy"
TOP_RATED = "rating"
NEWEST = "newest"
PRICE_HIGH_TO_LOW = "price-desc"
PRICE_LOW_TO_HIGH = "price-asc"
TITLE_A_TO_Z = "title-asc"
TITLE_Z_TO_A = "title-desc"

SORT_BY_CHOICES = [
    (RELEVANCY, _("Relevancy")), (TOP_RATED, _("Customer rating")), (NEWEST, _("Newest")),
    (PRICE_HIGH_TO_LOW, _("Price high to low")), (PRICE_LOW_TO_HIGH, _("Price low to high")),
    (TITLE_A_TO_Z, _("Title A to Z")), (TITLE_Z_TO_A, _("Title Z to A")),
]

SORT_BY_MAP = {
    TOP_RATED: '-rating', NEWEST: '-date_created', PRICE_HIGH_TO_LOW: '-effective_price',
    PRICE_LOW_TO_HIGH: 'effective_price', TITLE_A_TO_Z: 'title', TITLE_Z_TO_A: '-title',
}

# FILTERING
FILTER_BY_CHOICES = [
    ('exclude_out_of_stock', "Exclude Out Of Stock"),
    ('price__range', "Price Range"),
    ('width', "Width"),
    ('height', "Height"),
    ('material', 'Material'),
]


class ProductListAPIView(GenericAPIView):
    queryset = Product.browsable.browsable()
    # pagination_class = Paginator
    i_paginator = None

    # Extracting Dataset

    def prepare_data(self, request):
        self.base_queryset = Product.browsable.browsable()
        self.default_category = 'all'
        self.queryset = self.base_queryset
        self.out = {}
        self.title = 'All'
        self.product_range = None
        self.cat = None
        self.rc = None
        self.page_obj = None
        self.sort = request.GET.get('sort')
        self.search = request.GET.get('q')
        self.filter = request.GET.get('filter')
        self.offer_category = request.GET.get('offer_category')
        self.range = request.GET.get('range')
        self.pclass = request.GET.get('pclass')
        self.pincode = request.GET.get('pincode')
        self.brand = request.GET.get('brand')
        self.page_number = int(request.GET.get('page', '1'))
        self.page_size = int(request.GET.get('page_size', str(settings.DEFAULT_PAGE_SIZE)))
        self.only_favorite = bool(request.GET.get('only_favorite', False))

    def get(self, request, category='all'):
        self.category = category
        # extract
        self.prepare_data(request)

        # transform
        self.apply_primary_filter()
        self.find_recommended_class()
        # self.filter_favorite()
        self.filter_product_class()
        self.apply_filter()
        self.apply_search()

        # load
        # self.filter_stock()
        products_list = self.sort_products()
        self.paginate_dataset(products_list)
        serialized_products_list = self.load_paginated_data()
        self.load_seo()

        return Response(self.render_api(serialized_products_list))

    # Transforming Dataset

    def primary_range_selecter(self):
        _range = self.range
        if type(_range) is int or _range.isdigit():
            params = {'id': _range}
        else:
            params = {'slug': _range}
        product_range = Range.objects.filter(**params).first()
        if product_range:
            self.title = product_range.name
            self.queryset = product_range.all_products().filter(is_public=True)

    def category_filter(self):
        self.queryset, self.cat = category_filter(queryset=self.queryset, category_slug=self.category, return_as_tuple=True)
        self.title = self.cat.name

    def apply_primary_filter(self):
        _range = self.range
        _offer_category = self.offer_category
        if _range:
            self.primary_range_selecter()
        elif self.category != self.default_category:
            self.category_filter()

    def find_recommended_class(self):
        params = {'search': self.search, 'range': self.product_range, "category": self.cat, "pclass": self.pclass}
        self.rc = recommended_class(self.queryset, **params)
        self.product_class = ProductClass.objects.filter(pk=self.rc['id']).first()

    def filter_favorite(self):
        if self.only_favorite and self.request.user.is_authenticated:
            self.queryset = self.queryset.filter(id__in=self.request.user.product.all().values_list('id'))

    def filter_product_class(self):
        if self.product_class and (self.search or self.filter or self.category == self.default_category):
            self.queryset = self.queryset.filter(
                Q(product_class_id=self.pclass) | Q(parent__product_class_id=self.pclass))

    def apply_filter(self):
        if self.filter:
            """
            input = weight__in:25,30,35|price__gte:25|price__lte:45
            """
            self.queryset = apply_filter(queryset=self.queryset, _filter=self.filter, product_class=self.product_class)

    def apply_search(self):
        if self.search:
            self.queryset = apply_search(
                queryset=self.queryset,
                search=self.search,
                mode='_simple')  # | apply_search(queryset=queryset, search=_search, mode='_trigram',)
            self.title = f"Search: '{self.search}'"

    # Load Dataset
    def get_partners(self):
        zone = None
        if self.request.GET.get('pincode'):
            from apps.availability.facade import get_zone_from_pincode
            _zone = get_zone_from_pincode(self.request.GET.get('pincode'))
            zone = _zone.id
        if zone is None:
            zone: int = self.request.session.get('zone')  # zone => Zone.pk
        if zone:
            partner_ids = Zones.objects.filter(pk=zone).values_list('partner_id', flat=True)
        else:
            partner_ids = Zones.objects.order_by('-is_default_zone').values_list('partner_id', flat=True)
        return partner_ids

    def stocked_products(self):
        partner_ids = self.get_partners()

        stk_qs = StockRecord.objects.filter(
            partner_id__in=partner_ids, num_in_stock__gt=0,
        ).values_list('product_id', flat=True)
        child_selections = Q(Q(structure=Product.CHILD) & Q(parent_id__in=stk_qs))
        parent_selections = Q(Q(structure=Product.STANDALONE) & Q(id__in=stk_qs))
        return self.queryset.filter(parent_selections | child_selections)

    def filter_stock(self):
        self.queryset = self.stocked_products()

    def sort_products(self):
        if self.search:
            from fuzzywuzzy import fuzz
            return list(sorted(
                self.queryset[:160],
                key=lambda p: fuzz.token_sort_ratio(self.search.upper(), p.search_tags.upper()),
                reverse=True
            )) + list(self.queryset[160:])

        elif self.sort:
            _sort = [SORT_BY_MAP[key] for key in self.sort.split(',') if key and key in SORT_BY_MAP.keys()]
            qs = apply_sort(queryset=self.queryset, sort=_sort)
            return qs
        return self.queryset

    def paginate_dataset(self, products_list):
        page_number = int(self.request.GET.get('page', '1'))
        page_size = int(self.request.GET.get('page_size', str(settings.DEFAULT_PAGE_SIZE)))
        i_paginator = self.i_paginator = Paginator(object_list=products_list, per_page=page_size)  # Show 18 contacts per page.
        self.i_paginator.display_page_controls = False
        self.empty_list = False
        try:
            page_number = i_paginator.validate_number(page_number)
        except PageNotAnInteger:
            page_number = 1
        except EmptyPage:
            page_number = i_paginator.num_pages
            self.empty_list = True
        self.page_obj = i_paginator.get_page(page_number)

    def load_seo(self):
        self.cat_data = {}
        if self.cat:
            self.cat_data['seo_title'] = self.cat.seo_title
            self.cat_data['seo_description'] = self.cat.seo_description
            self.cat_data['seo_keywords'] = self.cat.seo_keywords
            self.cat_data['ogimage'] = self.request.build_absolute_uri(self.cat.ogimage.url) if self.cat.ogimage else None

    def render_api(self, serialized_products_list):
        return list_api_formatter(
            self.request, paginator=self.i_paginator, page_obj=self.page_obj,
            results=serialized_products_list, product_class=self.rc, title=self.title,
            bread_crumps=get_breadcrumb(self.search, self.cat, self.product_range), seo_fields=self.cat_data)

    def load_paginated_data(self):
        # return ProductSimpleListSerializer(self.page_obj.object_list, context=self.request).data
        product_serializer_class = ProductSimpleListSerializer
        product_data = {}
        cxt = {'request': self.request}
        for product in self.page_obj.object_list:
            # sr.product.selected_stock_record = sr
            if product.is_child:
                if product.parent not in product_data.keys():
                    product_data[product.parent] = product_serializer_class(
                        instance=product.parent,
                        context=cxt
                    ).data
                    product_data[product.parent]['variants'] = []
                product_data[product.parent]['variants'].append(
                    product_serializer_class(instance=product, context=cxt).data)
            elif product.is_standalone:  # parent or standalone
                product_data[product] = product_serializer_class(instance=product, context=cxt).data
                product_data[product]['variants'] = []
        return product_data.values()

product_list_new_pagination = ProductListAPIView.as_view()



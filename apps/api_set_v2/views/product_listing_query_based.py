from django.db import models, connection

from lib.product_utils.search import tag__combinations

from django.db.models import Q, Value, Prefetch, F
from django.dispatch import receiver
from django.http import Http404
from oscar.apps.analytics.models import ProductRecord, UserRecord, UserProductView
from oscar.apps.analytics.receivers import _update_counter
from oscar.apps.catalogue.signals import product_viewed
from oscar.apps.offer.models import Range
from django.conf import settings
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

from factory.django import get_model
from oscar.apps.offer.models import ConditionalOffer
from oscar.core.loading import get_class
from rest_framework.decorators import api_view
from rest_framework.generics import get_object_or_404, GenericAPIView
from rest_framework.response import Response

from apps.api_set_v2.serializers.catalogue import ProductSimpleListSerializer
from apps.api_set_v2.utils.product import get_optimized_product_dict
from apps.dashboard.custom.models import OfferBanner
from apps.partner.models import StockRecord
from lib.product_utils import category_filter, apply_filter, apply_search, apply_sort, recommended_class
from apps.catalogue.models import Product, ProductClass
from apps.utils.urls import list_api_formatter
from lib.cache import cache_library

get_product_search_handler_class = get_class(
    'catalogue.search_handlers', 'get_product_search_handler_class')


_ = lambda x: x


Category = get_model('catalogue', 'Category')
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
    ('exclude_out_of_stock', _("Exclude Out Of Stock")),
    ('price__range', _("Price Range")),
    ('width', _("Width")),
    ('height', _("Height")),
    ('material', _('Material')),
]


def get_breadcrumb(_search, cat, product_range):
    if cat:
        cats = cat.get_ancestors_and_self()
    else:
        class C:
            name = "All"
            slug = "all"
        cats = [C]
    out = [
        {"title": "Home", "url": '?'},
        *[{"title": c.name, "url": f'?category={c.slug}'} for c in cats],
    ]
    if product_range:
        out.append({"title": product_range.name, "url": f"?product_range={product_range.id}"})
    if _search:
        out.append({"title": f"Search: {_search}", "url": f"?q={_search}"})
    return out


def send_user_search(request, query):
    # Raise a signal for other apps to hook into for analytics
    Category.objects.filter(name__icontains=query.lower()).update(search_count=F('search_count')+1)
    #


@receiver(product_viewed)
def receive_product_view(sender, product, user, **kwargs):
    if kwargs.get('raw', False):
        return
    _update_counter(ProductRecord, 'num_views', {'product': product})
    if user and user.is_authenticated:
        _update_counter(UserRecord, 'num_product_views', {'user': user})
        UserProductView.objects.create(product=product, user=user)


@api_view()
def product_list(request, category='all', **kwargs):
    """
    PRODUCT LISTING API, (powering,  list /c/all/, /c/<category_slug>/,  )
    ===
    q = " A search term "
    product_range = '<product-range-id>'
    sort = any one from ['relevancy', 'rating', 'newest', 'price-desc', 'price-asc', 'title-asc', 'title-desc']
    filter = minprice:25::maxprice:45::available_only:1::color=Red,Black,Blue::weight:25,30,35::ram:4 GB,8 GB
        Where minprice, maxprice and  available_only are common for all.
        other dynamic parameters are available at  reverse('wnc-filter-options', kwarg={'pk': '<ProductClass: id>'})
    """
    _default_category = 'all'
    queryset = Product.browsable.browsable()
    _search = request.GET.get('q')
    _sort = request.GET.get('sort')
    _filter = request.GET.get('filter')
    _offer_category = request.GET.get('offer_category')
    _range = request.GET.get('range')
    _pclass = request.GET.get('pclass')
    _pincode = request.GET.get('pincode')
    _brand = request.GET.get('brand')

    page_number = int(request.GET.get('page', '1'))
    page_size = int(request.GET.get('page_size', str(settings.DEFAULT_PAGE_SIZE)))
    only_favorite = bool(request.GET.get('only_favorite', False))
    out = {}
    # search_handler = get_product_search_handler_class()(request.GET, request.get_full_path(), [])
    title = 'All'
    product_range = None
    cat = None

    if _range:
        if type(_range) is int or _range.isdigit():
            params = {'id': _range}
        else:
            params = {'slug': _range}
        product_range = Range.objects.filter(**params).first()
        if product_range:
            title = product_range.name
            queryset = product_range.all_products().filter(is_public=True)
    elif _offer_category:
        offer_banner_object = get_object_or_404(OfferBanner, code=_offer_category, offer__status=ConditionalOffer.OPEN)
        if offer_banner_object and offer_banner_object.product_range:
            title = offer_banner_object.product_range.name
            queryset = offer_banner_object.products().filter(is_public=True)
    elif category != _default_category:
        queryset, cat = category_filter(queryset=queryset, category_slug=category, return_as_tuple=True)
        title = cat.name

    params = {'search': _search, 'range': product_range, "category": cat, "pclass": _pclass}
    rc = recommended_class(queryset, **params)
    product_class = ProductClass.objects.filter(pk=rc['id']).first()

    if only_favorite and request.user.is_authenticated:
        queryset = queryset.browsable.filter(id__in=request.user.product.all().values_list('id'))

    if _pclass and (_search or category == _default_category):
        queryset = queryset.filter(product_class=_pclass)

    if _filter:
        """
        input = weight__in:25,30,35|price__gte:25|price__lte:45
        """
        queryset = apply_filter(queryset=queryset, _filter=_filter, product_class=product_class)

    if _search:
        mode = '_simple'
        if len(_search) <= 2:
            mode = '_simple'
        else:
            mode = '_trigram'
        queryset = apply_search(queryset=queryset, search=_search, mode="_simple")
        __qs = apply_search(queryset=queryset, search=_search, mode='_trigram',)
        queryset = queryset | __qs.annotate(priority=Value(4))
        title = f"Search: '{_search}'"
        # if queryset.count() < 5:
        #     queryset |= apply_search(queryset=queryset, search=_search, mode='_simple',)

    if _sort:
        # import pdb;pdb.set_trace()
        # queryset1 = StockRecord.objects.filter(product__in=queryset).select_related('product', 'partner')
        _sort = [SORT_BY_MAP[key] for key in _sort.split(',') if key and key in SORT_BY_MAP.keys()]
        queryset = apply_sort(queryset=queryset, sort=_sort)

    if _brand:
        queryset = queryset.filter(brand__name=_brand).select_related('Brand')

    def _inner():
        nonlocal queryset, page_number, title
        # queryset = queryset.browsable().base_queryset()
        paginator = Paginator(queryset, page_size)  # Show 18 contacts per page.
        empty_list = False
        try:
            page_number = paginator.validate_number(page_number)
        except PageNotAnInteger:
            page_number = 1
        except EmptyPage:
            page_number = paginator.num_pages
            empty_list = True
        page_obj = paginator.get_page(page_number)
        if not empty_list:
            from fuzzywuzzy import fuzz
            product_data = get_optimized_product_dict(qs=page_obj.object_list, request=request, ).values()
            # product_data = get_optimized_product_dict_for_listing(qs=page_obj.object_list, request=request, ).values()
            # product_data = serializer_class(page_obj.object_list, many=True, context={'request': request}).data
            if _search:
                product_data = sorted(product_data, key=lambda p: fuzz.token_sort_ratio(_search.lower(), p['priority'].lower()), reverse=True)

        else:
            product_data = []
        params = {'search': _search, 'range': product_range, "category": cat, "pclass": _pclass}
        rc = recommended_class(queryset, **params)
        cat_data = {}
        if cat:
            cat_data['seo_title'] = cat.seo_title
            cat_data['seo_description'] = cat.seo_description
            cat_data['seo_keywords'] = cat.seo_keywords
            cat_data['ogimage'] = request.build_absolute_uri(cat.ogimage.url) if cat.ogimage else None
        
        return list_api_formatter(request, paginator=paginator, page_obj=page_obj, results=product_data, product_class=rc, title=title,
                                  bread_crumps=get_breadcrumb(_search, cat, product_range), seo_fields=cat_data)
    response = Response(_inner())
    if _search and len(_search) > 3:
        send_user_search(request, response, _search)
    return response

    # if page_size == settings.DEFAULT_PAGE_SIZE and page_number <= 4 and not any([_search, _filter, _sort, _offer_category, _range, ]):
    #     c_key = cache_key.product_list__key.format(page_number, page_size, category)
    #     out = cache_library(c_key, cb=_inner, ttl=180)
    # else:
    #     out = _inner()
    # return Response(out)


class ProductListAPIView(GenericAPIView):
    """
        PRODUCT LISTING API, (powering,  list /c/all/, /c/<category_slug>/,  )
        ===
        q = " A search term "
        range = '<product-range-id>'
        sort = any one from ['relevancy', 'rating', 'newest', 'price-desc', 'price-asc', 'title-asc', 'title-desc']
        filter = minprice:25::maxprice:45::available_only:1::color=Red,Black,Blue::weight:25|30|35::ram:4 GB,8 GB
            Where minprice, maxprice and  available_only are common for all.
            other dynamic parameters are available at  reverse('wnc-filter-options', kwarg={'pk': '<ProductClass: id>'})
        """

    queryset = Product.browsable.browsable()
    # pagination_class = Paginator
    i_paginator = None

    # Extracting Dataset
    def prepare_product(self, qs):
        # return qs.select_related(
        #     'product_class',
        #     'parent__categories', 'parent__attributes', 'parent__attribute_values', 'parent__images',
        # ).prefetch_related(
        #     'categories', 'children', 'attributes', 'images', 'attribute_values',
        #     'children__parent', 'children__attributes',  'children__images',
        # )
        return qs.select_related('product_class', 'parent__brand', 'parent__product_class').prefetch_related(
            'categories',
            Prefetch('children', queryset=Product.objects.all().select_related(
                'product_class', 'parent__brand', 'parent__product_class'
            ).prefetch_related(
                'attributes', 'images', 'attribute_values'
            )),
            'attributes', 'images', 'attribute_values'
        )

    def prepare_data(self, request):
        # self.base_queryset = Product.browsable.browsable()
        self.base_queryset = Product.objects.all().filter(
            Q(structure__in=(Product.STANDALONE, Product.CHILD)), is_public=True
        )
        self.default_category = 'all'
        self.queryset = self.prepare_product(self.base_queryset)
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

    def log_qc(self, log_point, reset=True):
        cnt = len(connection.queries)
        self.qcount[log_point] = {
            'crossed': cnt,
            "delta": cnt - self.prev_qc
        }
        if reset:
            self.prev_qc = cnt

    def get(self, request, category='all'):
        self.out_log = out_log = {}
        self.qcount = {}
        self.category = category
        self.prev_qc = 0
        self.initial_qc = len(connection.queries)
        # extract
        self.prepare_data(request)
        out_log['0_initial'] = "data prepared!"
        out_log['1_prepare_data'] = "data prepared!"
        self.log_qc('01_initial')
        # transform
        self.apply_primary_filter()
        self.log_qc('02_primary_filter_applied')
        out_log['2_primary_filter_applied'] = f"Now count {self.queryset.count()}"
        self.find_recommended_class()
        out_log['3_rc'] = f"Now rc= {str(self.product_class)}"
        self.log_qc('03_rc')

        # self.filter_favorite()
        self.filter_product_class()
        out_log['4_pc_filter'] = f"Now rc filtering = {self.queryset.count()}"
        self.log_qc('04_pc_filter')

        self.queryset = self.queryset.annotate(rank=Value(5, output_field=models.IntegerField())).select_related('product_class')

        self.apply_filter()
        out_log['5_apply_filter'] = f"Now apply filter = {self.queryset.count()}"
        self.log_qc('05_apply_filter')

        # displayable_qs = self.queryset.exclude(structure=Product.PARENT)
        # child_qs = Product.objects.filter(parent_id__in=self.queryset.filter(structure=Product.PARENT).values_list('id'))
        # self.queryset = displayable_qs | child_qs
        self.apply_search()
        out_log['6_apply_search'] = f"Now apply search = {self.queryset.count()}"
        self.log_qc('06_apply_search with ' + str(self.queryset.count()) + " items.")
        q2 = self.queryset.values_list('id', 'parent_id')
        considered_parent_id = []
        allowed_ids = []
        for _id, parent_id in q2:
            if parent_id is None:
                allowed_ids.append(_id)
            if parent_id not in considered_parent_id:
                allowed_ids.append(_id)
                considered_parent_id.append(parent_id)

        self.queryset = self.queryset.filter(id__in=allowed_ids)

        out_log['6.5_apply_search'] = f"Now apply search = {self.queryset.count()}"
        self.log_qc('06.5_apply_search with ' + str(self.queryset.count()) + " items.")
        # self.queryset = self.queryset.exclude(structure=Product.PARENT)   TODO: uncomment
        products_list = self.sort_products()   # TODO: uncomment
        # products_list = self.queryset   # TODO: comment this line
        out_log['7_apply_sort'] = f"Now apply sort = {len(products_list)}"
        self.log_qc('07_apply_sort')
        self.paginate_dataset(products_list)
        out_log['8_paginated'] = f"Now apply sort = {len(products_list)}"
        self.log_qc('08_paginated')
        out_log['8_paginated_obj_list'] = f"page_obj.object_list = {len(self.page_obj.object_list)}"
        serialized_products_list = self.load_paginated_data()
        out_log['9_serialized_products_list_count'] = f"{len(serialized_products_list)}"
        self.log_qc('09_serialized_products_list_count')

        self.load_seo()
        self.log_qc('10_seo')
        if self.search and len(self.search) > 3:
            send_user_search(request, self.search)
        response = self.render_api(serialized_products_list, out_log=self.out_log, qcount=self.qcount)
        return Response(response)

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
            self.queryset = Product.get_abs_product(product_range.all_products())
        else:
            raise Http404()

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

        params = {'search': self.search, 'range': self.product_range, "category": self.cat,
                  "pclass": self.pclass, "preferred_cats": [self.cat, ]}
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
            input = weight__in:25|30|35::minprice:25::maxprice45
            
            ?filter=
            weight__in : 25|35|45
             minprice : 25,
             maxprice : 45,
             available_only : 1
             color: Red|Black|Blue
             ram:4 GB|8 GB
            """
            # removed product_class argument
            self.queryset = apply_filter(queryset=self.queryset, _filter=self.filter)

    def apply_search(self):
        if self.search:
            self.queryset = apply_search(
                queryset=self.queryset,
                search=self.search,
                mode='_trigram'
            ) #| apply_search(queryset=self.queryset, search=self.search, mode='_trigram',)
            # self.queryset = self.queryset.order_by('rank')
            self.title = f"You searched for: {self.search}"

    # Load Dataset

    def stocked_products(self):

        stk_qs = StockRecord.objects.filter(num_in_stock__gt=0).values_list('product_id', flat=True)
        child_selections = Q(Q(structure=Product.CHILD) & Q(parent_id__in=stk_qs))
        parent_selections = Q(Q(structure=Product.STANDALONE) & Q(id__in=stk_qs))
        return self.queryset.filter(parent_selections | child_selections)

    def filter_stock(self):
        self.queryset = self.stocked_products()

    def sort_products(self):
        # if self.search:
        #     combos = tag__combinations(self.search)
        #     qs = self.queryset[:60]
        #     for p in qs:
        #         p.custom_ranking = 0
        #         for term in combos:
        #             weight: Union[int, Any] = (term.count(' ') + 1) ** 2
        #             if term in p.search_tags:
        #                 p.custom_ranking += weight
        #     qs = list(sorted(qs, key=lambda p: p.custom_ranking, reverse=True))
        #     return qs + list(self.queryset[60:])
        # el
        if self.sort:
            _sort = [SORT_BY_MAP[key] for key in self.sort.split(',') if key and key in SORT_BY_MAP.keys()]
            self.queryset = apply_sort(queryset=self.queryset, sort=_sort)
        return self.queryset

    def paginate_dataset(self, products_list):
        page_number = int(self.request.GET.get('page', '1'))
        page_size = int(self.request.GET.get('page_size', str(settings.DEFAULT_PAGE_SIZE)))
        self.i_paginator = Paginator(object_list=products_list, per_page=page_size)  # Show 18 contacts per page.
        self.i_paginator.display_page_controls = False
        self.empty_list = False
        # import pdb;pdb.set_trace()
        try:
            page_number = self.i_paginator.validate_number(page_number)
        except PageNotAnInteger:
            page_number = 1
        except EmptyPage:
            page_number = self.i_paginator.num_pages
            self.empty_list = True
        self.page_obj = self.i_paginator.get_page(page_number)

    def load_seo(self):
        self.cat_data = {}
        if self.cat:
            self.cat_data['seo_title'] = self.cat.seo_title
            self.cat_data['seo_description'] = self.cat.seo_description
            self.cat_data['seo_keywords'] = self.cat.seo_keywords
            self.cat_data['ogimage'] = self.request.build_absolute_uri(self.cat.ogimage.url) if self.cat.ogimage else None

    def render_api(self, serialized_products_list, **kwargs):
        return list_api_formatter(
            self.request, paginator=self.i_paginator, page_obj=self.page_obj,
            results=serialized_products_list, product_class=self.rc, title=self.title,
            bread_crumps=get_breadcrumb(self.search, self.cat, self.product_range), seo_fields=self.cat_data, **kwargs)

    def load_paginated_data(self):
        # return ProductSimpleListSerializer(self.page_obj.object_list, context=self.request).data
        product_serializer_class = ProductSimpleListSerializer
        product_data = {}
        cxt = {'request': self.request}
        self.out_log['10_pagine'] = {}

        for product in self.page_obj.object_list:

            # sr.product.selected_stock_record = sr
            self.out_log['10_pagine'][f"{product.slug}__{product.id}"] = {"text": "loading " + ("parent " if product.is_child else "self"), "struct": product.structure }
            self.log_qc('10__' + f"{product.slug}__{product.id}")
            focuesd_product = product.parent if product.is_child else product
            product_data[product] = cache_library(
                f'listing_cached_product:{focuesd_product.id}',
                cb=lambda: product_serializer_class(
                    instance=focuesd_product, context=cxt
                ).data
            )
            # product_data[product]['price'] = ProductSimplePriceListSerializer(instance=focuesd_product, context=cxt).data['price']
            product_data[product]['variants'] = []
            parent = None
            if product.is_child:
                parent = product.parent
            elif product.is_parent:
                parent = product
            if hasattr(product, "rank"):
                product_data[product]['custom_ranking'] = getattr(product, "rank")
            else:
                product_data[product]['custom_ranking'] = 0

            if parent:
                selected = False
                self.out_log['10_pagine'][f"{product.slug}__{product.id}"]['varient_count'] = parent.children.all().count()
                product_data[product]['variants'] = []
                for pdt in parent.children.all():
                    product_data[product]['variants'].append(
                        product_serializer_class(pdt, context=cxt).data
                    )
                    self.log_qc('10__' + f"{product.slug}__{product.id}__varient:{pdt.id}", reset=True)

                for p in product_data[product]['variants']:
                    if p['id'] == product.id:
                        p.update({"is_selected": p['id'] == product.id})
                        product_data[product].update({
                            "primary_image": p['primary_image'],
                            "price": p['price'],
                            "title": p['title'],
                            "rating": p['rating'],
                            "review_count": p['review_count'],
                        })
                        selected = True
                    if hasattr(product, "rank"):
                        product_data[product]['custom_ranking'] = getattr(product, "rank", 0)
                    else:
                        product_data[product]['custom_ranking'] = 0

                if selected is False and product_data[product]['variants']:
                    ind = 0
                    min_price_val = float('inf')
                    min_price_index = 0
                    for variant in product_data[product]['variants']:
                        if variant['price']['effective_price'] < min_price_val:
                            min_price_val = variant['price']
                            min_price_index = ind
                        ind += 1
                    product_data[product]['variants'][min_price_index]['is_selected'] = True
        return product_data.values()
        # for product in self.page_obj.object_list:
        #     # sr.product.selected_stock_record = sr
        #     if product.is_child:
        #         if product.parent not in product_data.keys():
        #             product_data[product.parent] = product_serializer_class(
        #                 instance=product.parent,
        #                 context=cxt
        #             ).data
        #             product_data[product.parent]['variants'] = []
        #         product_data[product.parent]['variants'].append(
        #             product_serializer_class(instance=product, context=cxt).data)
        #     elif product.is_standalone:  # parent or standalone
        #         product_data[product] = product_serializer_class(instance=product, context=cxt).data
        #         product_data[product]['variants'] = []
        # return product_data.values()


product_list_new_pagination = ProductListAPIView.as_view()


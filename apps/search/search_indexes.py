import json

from django.core.serializers.json import DjangoJSONEncoder
from django.urls import reverse
from haystack import indexes
from oscar.apps.address.models import Country

from oscar.core.loading import get_class, get_model

# Load default strategy (without a user/request)
from apps.api_set.serializers.catalogue import custom_ProductListSerializer
from apps.api_set.serializers.mixins import ProductPriceFieldMixinLite, ProductPrimaryImageFieldMixin
from apps.catalogue.models import StockRecord
from apps.dashboard.custom.models import empty
from apps.partner.strategy import Selector
from apps.utils import purchase_info_lite_as_dict, image_not_found, dummy_purchase_info_lite_as_dict, LazyEncoder

is_solr_supported = get_class('search.features', 'is_solr_supported')

Country

class ProductIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(
        document=True, use_template=True,
        template_name='oscar/search/indexes/product/item_text.txt')
    pk = indexes.IntegerField(model_attr='pk', null=True)
    title = indexes.EdgeNgramField(model_attr='title', null=True)
    title_exact = indexes.CharField(model_attr='title', null=True, indexed=False)
    product_class = indexes.CharField(null=True, indexed=False)
    upc = indexes.CharField(model_attr="upc", null=True)

    # Fields for faceting
    category = indexes.MultiValueField(null=True, faceted=True)
    primary_image = indexes.CharField(null=True, faceted=True)
    stock_data = indexes.CharField(null=True, faceted=True)
    children = indexes.CharField(null=True, faceted=True)
    price = indexes.FloatField(null=True, faceted=True)
    num_in_stock = indexes.IntegerField(null=True, faceted=True)
    rating = indexes.IntegerField(null=True, faceted=True)

    # Spelling suggestions
    suggestions = indexes.FacetCharField()
    date_created = indexes.DateTimeField(model_attr='date_created')
    date_updated = indexes.DateTimeField(model_attr='date_updated')

    _strategy = None

    def get_model(self):
        return get_model('catalogue', 'Product')

    def index_queryset(self, using=None):
        # Only index browsable products (not each individual child product)
        return self.get_model().browsable.order_by('-date_updated')

    def read_queryset(self, using=None):
        return self.get_model().browsable.base_queryset()

    def prepare_product_class(self, obj):
        return obj.get_product_class().name

    def prepare_category(self, obj):
        categories = obj.get_categories().only('name')
        if len(categories) > 0:
            return [category.name for category in categories]

    def prepare_price(self, obj):
        skr = obj.stockrecords.order_by('price_excl_tax').first()
        if skr:
            return skr.price_excl_tax

    def prepare_primary_image(self, obj):
        return getattr(obj.primary_image(), 'original')

    def prepare_stock_data(self, obj):
        availability = StockRecord.objects.filter(product__parent=obj).exists()
        return dummy_purchase_info_lite_as_dict(**{
                'availability': availability,
                "availability_message": "Available" if availability else "Unavailable",
            })

    def get_stock_data(self, obj):
        """ stores as json """
        stock_records = obj.stockrecords.all()
        general_strategy = Selector().strategy()

        def _inner(stock_record):
            purchase_info = None
            if obj.is_parent:
                purchase_info = general_strategy.fetch_for_parent(obj)
            elif obj.has_stockrecords:
                purchase_info = general_strategy.fetch_for_product(obj, stock_record)

            availabilities = {
                'availability': purchase_info.availability.is_available_to_buy if purchase_info else False,
                "availability_message": (
                    purchase_info.availability.short_message if purchase_info else "No information available",
                )
            }
            return purchase_info_lite_as_dict(purchase_info, **availabilities)
        return json.dumps(
            obj={record.id: _inner(record) for record in stock_records},
            cls=DjangoJSONEncoder)

    def prepare_children(self, obj, price_serializer_mixin=ProductPriceFieldMixinLite(),
                         primary_image_serializer_mixin=ProductPrimaryImageFieldMixin(),
                         is_external_call=True, **kwargs):
        """ stores as json """
        primary_image_serializer_mixin.context = price_serializer_mixin.context = {
            'request': empty()
        }
        queryset = obj.children.all()
        return json.dumps({"result": [{
            "id": product.id,
            "title": product.title,
            "primary_image": primary_image_serializer_mixin.get_primary_image(product),
            "url": reverse('product-detail', kwargs={'pk': product.id}),
            "price": self.get_stock_data(product),
            "weight": getattr(
                product.attribute_values.filter(attribute__code='weight').first(), 'value', 'unavailable'
            ) if not product.is_parent else None,
            'variants': None
        } for product in queryset]})

    def prepare(self, obj):
        prepared_data = super().prepare(obj)

        # We use Haystack's dynamic fields to ensure that the title field used
        # for sorting is of type "string'.
        if is_solr_supported():
            prepared_data['title_s'] = prepared_data['title']

        # Use title to for spelling suggestions
        prepared_data['suggestions'] = prepared_data['text']

        return prepared_data

    def get_updated_field(self):
        """
        Used to specify the field used to determine if an object has been
        updated

        Can be used to filter the query set when updating the index
        """
        return 'date_updated'

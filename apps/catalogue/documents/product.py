from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from django.conf import settings
from elasticsearch_dsl import InnerDoc
from oscar.core.loading import get_model
from apps.partner.strategy import Selector

from apps.catalogue.documents.analyzers import html_strip, title_ngram_analyzer, lowercase

Product = get_model('catalogue', 'Product')
Category = get_model('catalogue', 'Category')
StockRecord = get_model('partner', 'StockRecord')


def remove_html_tags(text):
    """Remove html tags from a string"""
    import re
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)


class ProductInnerDocument(InnerDoc):
    title = fields.TextField(fields={
        'keyword': fields.KeywordField(),
        'n_gram': fields.TextField(analyzer=title_ngram_analyzer)}, fielddata=True)
    id = fields.KeywordField()
    is_public = fields.BooleanField(attr='is_public', default=True)
    price = fields.FloatField()
    slug = fields.KeywordField()


@registry.register_document
class ProductDocument(Document):
    id = fields.KeywordField(attr='id')
    title = fields.TextField(fields={
        'keyword': fields.KeywordField(normalizer=lowercase),
        'n_gram': fields.TextField(analyzer=title_ngram_analyzer)
    }, fielddata=True)
    description = fields.TextField(attr="description", analyzer=html_strip)
    price = fields.ObjectField()
    effective_price = fields.FloatField()
    category_slugs = fields.KeywordField()       # for filtering
    categories = fields.KeywordField()           # for search
    parent_categories = fields.KeywordField()    # for low preference Search

    slug = fields.TextField(attr="slug")
    brand = fields.KeywordField()
    is_public = fields.BooleanField(attr='is_public', default=True)
    # rating = fields.FloatField(attr='rating', default=0.0)
    rating_count = fields.IntegerField(default=0)

    structure = fields.TextField(attr="structure")
    image_url = fields.TextField()
    # parent = fields.ObjectField(ProductInnerDocument)
    # children = fields.NestedField(ProductInnerDocument)

    @staticmethod
    def prepare_description(instance):
        return remove_html_tags(instance.description)

    @staticmethod
    def prepare_price(instance):
        # TODO: Set checking for parent child and standalone
        strategy = Selector().strategy()
        purchase_info = strategy.fetch_for_product(product=instance)
        return {
            'effective_price': purchase_info.price.effective_price,
            'currency': purchase_info.price.currency,
            'excl_tax': purchase_info.price.excl_tax,
            'incl_tax': purchase_info.price.incl_tax,
            'is_tax_known': purchase_info.price.is_tax_known,
            'retail': purchase_info.price.retail,
            'tax': purchase_info.price.tax,
        }

    def prepare_effective_price(self, instance):
        return self.prepare_price(instance)['effective_price']

    @staticmethod
    def prepare_category_slugs(instance):
        return [n.slug for m in instance.categories.all() for n in m.get_ancestors_and_self()]

    def prepare_parent_categories(self, instance):
        all_cats = instance.categories.all()
        all_cats_name = []
        for cat in all_cats:
            all_cats_name.extend([c.name for c in cat.get_ancestors()])
        return list(set([m.lower() for m in all_cats_name]))

    def prepare_brand(self, instance):
        return ""

    @staticmethod
    def prepare_categories(instance):
        return [m.lower() for m in instance.categories.all().values_list('name', flat=True)]

    @staticmethod
    def prepare_image_url(instance):
        return [m.lower() for m in instance.categories.all().values_list('name', flat=True)]

    @staticmethod
    def prepare_rating_count(instance):
        return 0

    class Index:
        name = settings.ELASTIC__PRODUCT_INDEX
        settings = {'number_of_shards': 1, 'number_of_replicas': 0}

    class Django:
        model = Product

        fields = [
            # 'id',
            # 'title',
            # 'is_public',
            'rating',
        ]
        ignore_signals = False
        auto_refresh = True
        related_models = [StockRecord, Category]    # Optional: to ensure the Car will be re-saved when Manufacturer or Ad is updated

    def get_queryset(self):
        """Not mandatory but to improve performance we can select related in one sql request"""
        return super().get_queryset().browsable().prefetch_related('categories')

    def get_instances_from_related(self, related_instance):
        """ If related_models is set, define how to retrieve the Car instance(s) from the related model.
        The related_models option should be used with caution because it can lead in the index
        to the updating of a lot of items.
        """
        if isinstance(related_instance, StockRecord):
            return related_instance.product
        if isinstance(related_instance, Category):
            return related_instance.stockrecords.all()


"""
# Author : Atley Varghese
# Project : Unknown

class RetailerProductInnerDocument(InnerDoc):
    title = Text(fields={'keyword': Keyword(), 'n_gram': Text(analyzer=title_ngram_analyzer)}, fielddata=True)
    product_id = Keyword()
    show_on_website = Boolean()
    available_stores = Keyword()
    upc = Text()
    price = Float()
    max_item_per_cart = Integer()
    slug = Text()


@retailer_product.doc_type
class RetailerProductDocument(DocType):
    id = Integer()
    title = Text(fields={'keyword': Keyword(normalizer=lowercase), 'n_gram': Text(analyzer=title_ngram_analyzer)}, fielddata=True)
    upc = Text()
    brand = Keyword()
    categories = Keyword()
    category_names = Text()
    is_active = Boolean()
    product_id = Keyword()
    price_currency = Text()
    max_item_per_cart = Integer()
    price = Float()
    schema = Keyword()
    structure = Text()
    slug = Text()
    image_full_url = Text()
    added_at = Date()
    available_stores = Keyword()
    delivery_methods = Keyword()
    children = Nested(RetailerProductInnerDocument)

=========================================
RetailerProductDocument.search().filter(
        "terms", 
        delivery_methods=delivery_methods
    ).query(
        Q_filter("terms", upc=rewards)
        |Q_filter("nested", path="children", query=Q_filter("terms", children__upc=rewards))
    ).query(
        Q_filter("multi_match", query=primary_search_query,fields=['title', 'category_names', 'brand', 'upc', 'title.n_gram^.1'])
    )

"""








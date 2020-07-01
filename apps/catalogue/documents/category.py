from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from django.conf import settings
from oscar.core.loading import get_model

Category = get_model('catalogue', 'Category')
#
#
# @registry.register_document
# class CategoryDocument(Document):
#     slug = fields.KeywordField(attr="slug")
#     name = fields.KeywordField(attr="name")
#     description = fields.TextField(attr="description")
#     image = fields.TextField(attr="slug")
#     depth = fields.IntegerField(attr="slug")
#     numchild = fields.IntegerField(attr="slug")
#     path = fields.KeywordField(attr="slug")
#     # children = fields.NestedField(CategoryDocument)
#
#     class Index:
#         name = settings.ELASTIC__CATEGORY_INDEX
#         settings = {'number_of_shards': 1,
#                     'number_of_replicas': 0}
#
#     class Django:
#         model = Category
#         fields = ['id', 'name', 'description', 'image', 'depth', 'numchild', 'path', ]
#         ignore_signals = False
#         auto_refresh = True
#
#     def queryset(self):
#         return super(CategoryDocument, self).queryset().exclude(name="Featured", depth=0)
#


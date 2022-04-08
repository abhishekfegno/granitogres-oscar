from django.utils.translation import ungettext_lazy
from django_tables2 import LinkColumn, TemplateColumn, A
from oscar.apps.dashboard.tables import DashboardTable

from apps.catalogue.models import Brand, Product360Image


class BrandTable(DashboardTable):
    name = LinkColumn('dashboard:catalogue-brand-update', args=[A('pk')])

    icon = "sitemap"
    caption = ungettext_lazy("%s Brand", "%s Brands")

    class Meta(DashboardTable.Meta):
        model = Brand
        fields = ('name', )


class Product360ImageTable(DashboardTable):
    id = LinkColumn('dashboard:catalogue-product360-update', args=[A('pk')])
    title = LinkColumn('dashboard:catalogue-product360-update', args=[A('pk')])

    icon = "sitemap"
    caption = ungettext_lazy("%s 360 Image", "%s 360 Images")

    class Meta(DashboardTable.Meta):
        model = Product360Image
        fields = ('id', 'title', 'description', 'image', 'product', )


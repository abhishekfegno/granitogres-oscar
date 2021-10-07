from django.utils.translation import ungettext_lazy
from django_tables2 import LinkColumn, TemplateColumn, A
from oscar.apps.dashboard.tables import DashboardTable

from apps.catalogue.models import Brand


class BrandTable(DashboardTable):
    name = LinkColumn('dashboard:catalogue-brand-update', args=[A('pk')])

    icon = "sitemap"
    caption = ungettext_lazy("%s Brand", "%s Brands")

    class Meta(DashboardTable.Meta):
        model = Brand
        fields = ('name', )

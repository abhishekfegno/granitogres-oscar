import oscar.apps.dashboard.ranges.apps as apps
from oscar.core.loading import get_class


class RangesDashboardConfig(apps.RangesDashboardConfig):
    name = 'apps.dashboard.ranges'

    def ready(self):
        super().ready()
        self.list_view = get_class('dashboard.ranges.views', 'RangeListView')
        self.create_view = get_class('dashboard.ranges.views', 'RangeCreateView')
        self.update_view = get_class('dashboard.ranges.views', 'RangeUpdateView')
        self.delete_view = get_class('dashboard.ranges.views', 'RangeDeleteView')
        self.products_view = get_class('dashboard.ranges.views', 'RangeProductListView')
        self.reorder_view = get_class('dashboard.ranges.views', 'RangeReorderView')
import oscar.apps.dashboard.orders.apps as apps
from oscar.core.loading import get_class


class OrdersDashboardConfig(apps.OrdersDashboardConfig):
    name = 'apps.dashboard.orders'
    label = 'orders_dashboard'

    def ready(self):
        super(OrdersDashboardConfig, self).ready()
        from apps.dashboard.orders.views import OrderDetailView
        self.order_detail_view = OrderDetailView




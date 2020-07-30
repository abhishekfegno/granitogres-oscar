import oscar.apps.order.apps as apps


class OrderConfig(apps.OrderConfig):
    name = 'apps.order'

    def ready(self):
        from apps.order import signal_receivers


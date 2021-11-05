from django.apps import AppConfig


class DelhiveryConfig(AppConfig):
    name = 'apps.couriers.delhivery'

    def ready(self):
        from . import signals

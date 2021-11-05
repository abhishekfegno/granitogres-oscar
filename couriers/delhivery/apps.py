from django.apps import AppConfig


class DelhiveryConfig(AppConfig):
    name = 'couriers.delhivery'

    def ready(self):
        from . import signals

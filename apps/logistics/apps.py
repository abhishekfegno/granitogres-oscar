from django.apps import AppConfig


class LogisticsConfig(AppConfig):
    name = 'apps.logistics'

    def ready(self):
        from . import signal_receivers


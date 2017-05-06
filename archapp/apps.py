from django.apps import AppConfig


class ArchappConfig(AppConfig):
    name = 'archapp'

    def ready(self):
        import archapp.signals


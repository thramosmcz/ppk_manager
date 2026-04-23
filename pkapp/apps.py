from django.apps import AppConfig


class PkappConfig(AppConfig):
    name = 'pkapp'

    def ready(self):
        import pkapp.signals  # noqa

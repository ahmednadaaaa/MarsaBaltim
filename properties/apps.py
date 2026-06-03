from django.apps import AppConfig


class PropertiesConfig(AppConfig):
    name = 'properties'

    def ready(self):
        from .signals import connect_image_optimization
        connect_image_optimization()

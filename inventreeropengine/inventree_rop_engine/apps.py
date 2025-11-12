"""Django config for the inventreeropengine plugin."""

from django.apps import AppConfig

class inventreeropengineConfig(AppConfig):
    """Config class for the inventreeropengine plugin."""

    name = 'inventree_rop_engine'

    def ready(self):
        """This function is called whenever the inventreeropengine plugin is loaded."""
        ...

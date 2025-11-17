from django.apps import AppConfig


class InventoryConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "inventory"
    
    def ready(self):
        """Import signals when app is ready."""
        from . import signals  # noqa: F401 to register signal handlers


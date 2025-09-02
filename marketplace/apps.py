from django.apps import AppConfig


class MarketplaceConfig(AppConfig):
    """
    Application configuration for the marketplace app.

    This class specifies the default primary key field type and the application name.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "marketplace"

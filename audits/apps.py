from django.apps import AppConfig


class AuditsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "audits"

    def ready(self):
        # Import signal handlers
        from . import signals  # noqa: F401

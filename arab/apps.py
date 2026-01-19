from django.apps import AppConfig

class ArabConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "arab"

    def ready(self):
        from . import signals  # noqa

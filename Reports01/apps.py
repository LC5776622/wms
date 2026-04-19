from django.apps import AppConfig


class Reports01Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Reports01'

    def ready(self):
        import Reports01.signals
from django.apps import AppConfig

class RatesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'rates'

    def ready(self):
        import sys
        if 'manage.py' in sys.argv and ('migrate' in sys.argv or 'makemigrations' in sys.argv or 'check' in sys.argv):
            return
        # Removed automatic call to RateService.get_cached_rates() to avoid
        # accessing the database during app initialization and to avoid
        # blocking startup on network issues.
        print("✅ PanAfric Rate Engine ready (Lazy initialization)")
from django.apps import AppConfig

class BookingplatformConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bookingplatform'

    def ready(self):
        import bookingplatform.signals

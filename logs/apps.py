"""
Logs app configuration.
"""
from django.apps import AppConfig


class LogsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'logs'
    
    def ready(self):
        # Import logging utils to initialize logging
        from . import utils

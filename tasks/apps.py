from django.apps import AppConfig


class TasksConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tasks'

    def ready(self):
        # Start background automated email notification scheduler safely
        try:
            from .email_scheduler import start_notification_scheduler
            start_notification_scheduler()
        except Exception:
            pass



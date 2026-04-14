from django.apps import AppConfig


class UsersConfig(AppConfig):
    """
    Configuration class for the 'users' Django app.

    This class defines default settings for the app, including:
    - Default auto field type for model primary keys.
    - App name as used in INSTALLED_APPS.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'

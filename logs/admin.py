from django.apps import apps
from django.contrib import admin
from django.contrib.admin.sites import AlreadyRegistered


PROJECT_APP_LABELS = {
    'account',
    'cards',
    'control',
    'order',
    'withdrawal',
    'notification',
    'logs',
}


def register_unregistered_project_models() -> None:
    """
    Fallback registration:
    register any project model that doesn't already have an admin class.
    """
    for model in apps.get_models():
        if model._meta.app_label not in PROJECT_APP_LABELS:
            continue
        try:
            admin.site.register(model)
        except AlreadyRegistered:
            # Model already has an explicit/custom admin registration.
            pass


register_unregistered_project_models()

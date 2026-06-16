from .models import PushNotificationToken



def deactivate_token(token):
    PushNotificationToken.objects.filter(token=token).update(is_active=False)
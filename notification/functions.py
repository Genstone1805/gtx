from .models import PushNotificationSubscriber



def deactivate_token(token):
    PushNotificationSubscriber.objects.filter(token=token).update(is_active=False)
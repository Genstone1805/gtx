from django.urls import path
from .views import CreateGiftCardOrderView

urlpatterns = [
    path('create/', CreateGiftCardOrderView.as_view(), name='create_order'),
]

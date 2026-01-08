from django.urls import path
from .views import CreateGiftStoreView

urlpatterns = [
    path('create-gift-store/', CreateGiftStoreView.as_view(), name="create_gift_store_view"),
] 
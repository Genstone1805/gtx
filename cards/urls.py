from django.urls import path
from .views import GiftCardStoreListView

urlpatterns = [
    path('gift-card-stores/', GiftCardStoreListView.as_view(), name="gift_card_store_list_view"),
] 
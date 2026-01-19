from django.urls import path
from .views import GiftCardStoreListView, GiftCardListView

urlpatterns = [
    path('gift-card-stores/', GiftCardStoreListView.as_view(), name="gift_card_store_list_view"),
    path('gift-cards/', GiftCardListView.as_view(), name="gift_card_list_view"),
] 
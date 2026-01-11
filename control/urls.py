from django.urls import path
from .views import (
  CreateGiftStoreView,
  CreateGiftCardView,
  GiftStoreListView,
  GiftCardListView,
  GiftCardRetrieveUpdateDestroyView,
  GiftStoreRetrieveUpdateDestroyView,
  PendingLevel2CredentialsListView,
  PendingLevel3CredentialsListView,
  Level2CredentialApprovalView,
  Level3CredentialApprovalView
  )

urlpatterns = [
    path('create-gift-store/', CreateGiftStoreView.as_view(), name="create_gift_store_view"),
    path('create-gift-card/', CreateGiftCardView.as_view(), name="create_gift_card_view"),
    path('list-gift-stores/', GiftStoreListView.as_view(), name="list_gift_stores_view"),
    path('list-gift-cards/', GiftCardListView.as_view(), name="list_gift_cards_view"),
    path('get-gift-card/<int:pk>/', GiftCardRetrieveUpdateDestroyView.as_view(), name="get_gift_cards_view"),
    path('get-gift-store/<int:pk>/', GiftStoreRetrieveUpdateDestroyView.as_view(), name="get_gift_store_view"),

    # Credential approvals
    path('pending/level2/', PendingLevel2CredentialsListView.as_view(), name="pending_level2_list"),
    path('pending/level3/', PendingLevel3CredentialsListView.as_view(), name="pending_level3_list"),
    path('approve/level2/<int:credential_id>/', Level2CredentialApprovalView.as_view(), name="approve_level2"),
    path('approve/level3/<int:credential_id>/', Level3CredentialApprovalView.as_view(), name="approve_level3"),
] 
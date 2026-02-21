from django.urls import path
from .views import (
    UserBalanceView,
    WithdrawalListView,
    WithdrawalCreateView,
    WithdrawalDetailView,
    WithdrawalCancelView,
)

app_name = 'withdrawal'

urlpatterns = [
    # User endpoints
    path('balance/', UserBalanceView.as_view(), name='user-balance'),
    path('requests/', WithdrawalListView.as_view(), name='withdrawal-list'),
    path('requests/create/', WithdrawalCreateView.as_view(), name='withdrawal-create'),
    path('requests/<int:pk>/', WithdrawalDetailView.as_view(), name='withdrawal-detail'),
    path('requests/<int:pk>/cancel/', WithdrawalCancelView.as_view(), name='withdrawal-cancel'),
]

from django.urls import path
from .views import (
    UserBalanceView,
    WithdrawalListView,
    WithdrawalCreateView,
    WithdrawalDetailView,
    WithdrawalCancelView,
    AdminWithdrawalListView,
    AdminWithdrawalDetailView,
    AdminWithdrawalProcessView,
    AdminWithdrawalAuditLogView,
    AdminPendingWithdrawalsCountView,
)

app_name = 'withdrawal'

urlpatterns = [
    # User endpoints
    path('balance/', UserBalanceView.as_view(), name='user-balance'),
    path('requests/', WithdrawalListView.as_view(), name='withdrawal-list'),
    path('requests/create/', WithdrawalCreateView.as_view(), name='withdrawal-create'),
    path('requests/<int:pk>/', WithdrawalDetailView.as_view(), name='withdrawal-detail'),
    path('requests/<int:pk>/cancel/', WithdrawalCancelView.as_view(), name='withdrawal-cancel'),

    # Admin endpoints
    path('admin/requests/', AdminWithdrawalListView.as_view(), name='admin-withdrawal-list'),
    path('admin/requests/<int:pk>/', AdminWithdrawalDetailView.as_view(), name='admin-withdrawal-detail'),
    path('admin/requests/<int:pk>/process/', AdminWithdrawalProcessView.as_view(), name='admin-withdrawal-process'),
    path('admin/requests/<int:withdrawal_id>/audit-log/', AdminWithdrawalAuditLogView.as_view(), name='admin-withdrawal-audit-log'),
    path('admin/pending-count/', AdminPendingWithdrawalsCountView.as_view(), name='admin-pending-withdrawals-count'),
]

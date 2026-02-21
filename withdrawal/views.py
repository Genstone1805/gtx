from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Sum

from .models import Withdrawal, WithdrawalAuditLog
from .serializers import (
    WithdrawalCreateSerializer,
    WithdrawalListSerializer,
    WithdrawalDetailSerializer,
    WithdrawalApprovalSerializer,
    WithdrawalAuditLogSerializer,
    UserBalanceSerializer,
)
from account.models import UserProfile
from notification.services import notify_withdrawal_status_changed


class UserBalanceView(APIView):
    """Get current user's balance information."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = UserBalanceSerializer(user)
        return Response(serializer.data)


class WithdrawalListView(ListAPIView):
    """List all withdrawals for the authenticated user."""
    permission_classes = [IsAuthenticated]
    serializer_class = WithdrawalListSerializer

    def get_queryset(self):
        return Withdrawal.objects.filter(user=self.request.user).order_by('-created_at')


class WithdrawalCreateView(APIView):
    """Create a new withdrawal request."""
    permission_classes = [IsAuthenticated]
    serializer_class = WithdrawalCreateSerializer

    @transaction.atomic
    def post(self, request):
        user = request.user

        # Check if user has a transaction PIN set
        if not user.has_pin:
            raise PermissionDenied("You must create a transaction PIN before making withdrawals.")

        # Verify transaction PIN
        pin = request.data.get('transaction_pin')
        if not pin:
            raise ValidationError({"transaction_pin": "Transaction PIN is required."})
        
        if not user.check_transaction_pin(pin):
            raise ValidationError({"transaction_pin": "Incorrect transaction PIN."})

        serializer = self.serializer_class(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        withdrawal = serializer.save()

        # Create audit log
        WithdrawalAuditLog.objects.create(
            withdrawal=withdrawal,
            action='created',
            performed_by=user,
            details=f"Withdrawal request created for ${withdrawal.amount}",
            new_status='Pending',
        )

        return Response({
            'detail': 'Withdrawal request created successfully.',
            'withdrawal_id': withdrawal.id,
            'amount': str(withdrawal.amount),
            'status': withdrawal.status,
        }, status=status.HTTP_201_CREATED)


class WithdrawalDetailView(RetrieveAPIView):
    """Get detailed view of a specific withdrawal."""
    permission_classes = [IsAuthenticated]
    serializer_class = WithdrawalDetailSerializer
    queryset = Withdrawal.objects.all()

    def get_object(self):
        obj = super().get_object()
        # Users can only view their own withdrawals (unless admin)
        if not self.request.user.is_staff and obj.user != self.request.user:
            raise PermissionDenied("You don't have permission to view this withdrawal.")
        return obj


class WithdrawalCancelView(APIView):
    """Cancel a pending withdrawal request."""
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, pk):
        user = request.user
        
        try:
            withdrawal = Withdrawal.objects.get(pk=pk)
        except Withdrawal.DoesNotExist:
            raise ValidationError({"detail": "Withdrawal not found."})

        # Only the owner can cancel
        if withdrawal.user != user:
            raise PermissionDenied("You don't have permission to cancel this withdrawal.")

        if not withdrawal.can_cancel():
            raise ValidationError({
                "detail": f"Cannot cancel withdrawal with status: {withdrawal.status}"
            })

        previous_status = withdrawal.status
        withdrawal.cancel()

        # Create audit log
        WithdrawalAuditLog.objects.create(
            withdrawal=withdrawal,
            action='cancelled',
            performed_by=user,
            details="Withdrawal cancelled by user",
            previous_status=previous_status,
            new_status='Cancelled',
        )

        return Response({
            'detail': 'Withdrawal cancelled successfully.',
            'status': withdrawal.status,
        })


# Admin Views

class AdminWithdrawalListView(ListAPIView):
    """List all withdrawal requests (admin only)."""
    permission_classes = [IsAdminUser]
    serializer_class = WithdrawalListSerializer

    def get_queryset(self):
        queryset = Withdrawal.objects.all().order_by('-created_at')
        
        # Filter by status if provided
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        # Filter by user if provided
        user_param = self.request.query_params.get('user_id')
        if user_param:
            queryset = queryset.filter(user_id=user_param)
        
        return queryset


class AdminWithdrawalDetailView(RetrieveAPIView):
    """Get detailed view of a specific withdrawal (admin only)."""
    permission_classes = [IsAdminUser]
    serializer_class = WithdrawalDetailSerializer
    queryset = Withdrawal.objects.all()


class AdminWithdrawalProcessView(APIView):
    """Approve or reject a withdrawal request (admin only)."""
    permission_classes = [IsAdminUser]
    serializer_class = WithdrawalApprovalSerializer

    @transaction.atomic
    def post(self, request, pk):
        admin_user = request.user
        
        try:
            withdrawal = Withdrawal.objects.get(pk=pk)
        except Withdrawal.DoesNotExist:
            raise ValidationError({"detail": "Withdrawal not found."})

        if withdrawal.status != 'Pending':
            raise ValidationError({
                "detail": f"Cannot process withdrawal with status: {withdrawal.status}. Only pending withdrawals can be processed."
            })

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        action = serializer.validated_data['action']
        reason = serializer.validated_data.get('reason', '')
        transaction_reference = serializer.validated_data.get('transaction_reference', '')
        admin_notes = serializer.validated_data.get('admin_notes', '')

        previous_status = withdrawal.status

        if action == 'approve':
            withdrawal.approve(
                admin_user=admin_user,
                transaction_reference=transaction_reference
            )
            if admin_notes:
                withdrawal.admin_notes = admin_notes
                withdrawal.save()

            # Create audit log
            WithdrawalAuditLog.objects.create(
                withdrawal=withdrawal,
                action='approved',
                performed_by=admin_user,
                details=f"Withdrawal approved. Transaction ref: {transaction_reference}",
                previous_status=previous_status,
                new_status='Approved',
            )

            # Send notification
            notify_withdrawal_status_changed(
                user=withdrawal.user,
                withdrawal=withdrawal,
                new_status='Approved',
                amount=float(withdrawal.amount),
            )

            return Response({
                'detail': f'Withdrawal approved successfully. Amount ${withdrawal.amount} has been deducted from user\'s withdrawable balance.',
                'status': withdrawal.status,
                'transaction_reference': withdrawal.transaction_reference,
            })

        else:  # reject
            withdrawal.reject(admin_user=admin_user, reason=reason)
            if admin_notes:
                withdrawal.admin_notes = admin_notes
                withdrawal.save()

            # Create audit log
            WithdrawalAuditLog.objects.create(
                withdrawal=withdrawal,
                action='rejected',
                performed_by=admin_user,
                details=f"Withdrawal rejected. Reason: {reason}",
                previous_status=previous_status,
                new_status='Rejected',
            )

            # Send notification
            notify_withdrawal_status_changed(
                user=withdrawal.user,
                withdrawal=withdrawal,
                new_status='Rejected',
                amount=float(withdrawal.amount),
            )

            return Response({
                'detail': f'Withdrawal rejected. Reason: {reason}',
                'status': withdrawal.status,
            })


class AdminWithdrawalAuditLogView(ListAPIView):
    """List audit logs for a specific withdrawal (admin only)."""
    permission_classes = [IsAdminUser]
    serializer_class = WithdrawalAuditLogSerializer

    def get_queryset(self):
        withdrawal_id = self.kwargs.get('withdrawal_id')
        return WithdrawalAuditLog.objects.filter(
            withdrawal_id=withdrawal_id
        ).order_by('-created_at')


class AdminPendingWithdrawalsCountView(APIView):
    """Get count of pending withdrawals (for admin dashboard)."""
    permission_classes = [IsAdminUser]

    def get(self, request):
        pending_count = Withdrawal.objects.filter(status='Pending').count()
        pending_total = Withdrawal.objects.filter(
            status='Pending'
        ).aggregate(total=Sum('amount'))['total'] or 0

        return Response({
            'pending_count': pending_count,
            'pending_total': str(pending_total),
        })

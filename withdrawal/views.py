from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from .models import Withdrawal, WithdrawalAuditLog
from .serializers import (
    WithdrawalCreateSerializer,
    WithdrawalListSerializer,
    WithdrawalDetailSerializer,
    UserBalanceSerializer,
)
from account.models import UserProfile


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

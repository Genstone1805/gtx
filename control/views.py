import json
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAdminUser
from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.db import transaction
from decimal import Decimal
from django.db.models import Sum

from cards.models import GiftCardStore, GiftCardNames
from account.models import Level2Credentials, Level3Credentials, UserProfile
from order.models import GiftCardOrder
from withdrawal.models import Withdrawal, WithdrawalAuditLog
from .serializers import (
   CreateGiftStoreSerializer,
   CreateGiftCardSerializer,
   GiftStoreListSerializer,
   GiftCardListSerializer,
   UpdateGiftStoreSerializer,
   Level2CredentialsPendingSerializer,
   Level3CredentialsPendingSerializer,
   CredentialApprovalSerializer,
   PendingOrderSerializer,
   OrderStatusUpdateSerializer,
   WithdrawalListSerializer,
   WithdrawalDetailSerializer,
   WithdrawalApprovalSerializer,
   WithdrawalAuditLogSerializer,
   )
from notification.services import notify_kyc_status_changed, notify_balance_updated, notify_withdrawal_status_changed


def parse_querydict(query_dict):
    data = {}

    for key in query_dict.keys():
        value = query_dict.get(key)

        # Skip if value is a file upload (keep as-is)
        if hasattr(value, 'read'):
            data[key] = value
            continue

        # Try to parse as JSON (for arrays/objects passed as strings)
        if isinstance(value, str):
            stripped = value.strip()
            if stripped.startswith(('[', '{')):
                try:
                    data[key] = json.loads(stripped)
                    continue
                except json.JSONDecodeError:
                    pass

        # Default: use the value as-is (strip whitespace for strings)
        data[key] = value.strip() if isinstance(value, str) else value

    return data

class CreateGiftStoreView(APIView):
  permission_classes = [IsAdminUser]
  serializer_class = CreateGiftStoreSerializer

  def post(self, request, *args, **kwargs):
    # user = request.user
    data = parse_querydict(request.data)
    serializer = self.serializer_class(data = data)
    try:
      serializer.is_valid(raise_exception=True)
      cards = serializer.validated_data.pop("cards", [])
      store = GiftCardStore.objects.create(**serializer.validated_data)
      if cards:
        for card in cards:
          GiftCardNames.objects.create(store=store, **card)
      return Response("Store Created", status=status.HTTP_200_OK)
    except Exception as e:
      return Response(str(e), status=400)

class GiftCardListView(ListAPIView):
  permission_classes = [IsAdminUser]
  serializer_class = GiftCardListSerializer
  queryset = GiftCardNames.objects.all()

class GiftStoreListView(ListAPIView):
  permission_classes = [IsAdminUser]
  serializer_class = GiftStoreListSerializer
  queryset = GiftCardStore.objects.all()

class CreateGiftCardView(APIView):
  permission_classes = [IsAdminUser]
  serializer_class = CreateGiftCardSerializer

  def post(self, request, *args, **kwargs):
    data = request.data
    serializer = self.serializer_class(data = data)
    
    try:
      serializer.is_valid(raise_exception=True)
      GiftCardNames.objects.create(**serializer.validated_data)
      return Response("Gift Card Created", status=status.HTTP_200_OK)
    except Exception as e:
      return Response(str(e), status=400)
    
class GiftCardRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
  permission_classes = [IsAdminUser]
  serializer_class = CreateGiftCardSerializer
  lookup_field = "pk"
  queryset = GiftCardNames.objects.all()
    
class GiftStoreRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
  permission_classes = [IsAdminUser]
  serializer_class = UpdateGiftStoreSerializer
  lookup_field = "pk"
  queryset = GiftCardStore.objects.all()


class PendingLevel2CredentialsListView(ListAPIView):
    """List all pending Level 2 credential submissions."""
    permission_classes = [IsAdminUser]
    serializer_class = Level2CredentialsPendingSerializer

    def get_queryset(self):
        return Level2Credentials.objects.filter(status='Pending')


class PendingLevel3CredentialsListView(ListAPIView):
    """List all pending Level 3 credential submissions."""
    permission_classes = [IsAdminUser]
    serializer_class = Level3CredentialsPendingSerializer

    def get_queryset(self):
        return Level3Credentials.objects.filter(status='Pending')


class Level2CredentialApprovalView(APIView):
    """Approve or reject Level 2 credentials."""
    permission_classes = [IsAdminUser]

    def post(self, request, credential_id):
        credentials = get_object_or_404(Level2Credentials, id=credential_id)

        if credentials.status != 'Pending':
            return Response(
                {'detail': f'Credentials already processed. Status: {credentials.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = CredentialApprovalSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        action = serializer.validated_data['action']

        # Find the user associated with these credentials
        user = UserProfile.objects.filter(level2_credentials=credentials).first()
        if not user:
            return Response(
                {'detail': 'No user associated with these credentials.'},
                status=status.HTTP_404_NOT_FOUND
            )

        if action == 'approve':
            credentials.status = 'Approved'
            credentials.approved = True
            credentials.save()

            # Upgrade user to Level 2
            user.level = 'Level 2'
            user.transaction_limit = Decimal('5000000.00')
            user.save()
            notify_kyc_status_changed(user=user, level='2', new_status='Approved')

            return Response(
                {'detail': f'Level 2 credentials approved for {user.email}. Transaction limit increased to 5,000,000.'},
                status=status.HTTP_200_OK
            )
        else:
            credentials.status = 'Rejected'
            credentials.approved = False
            credentials.save()
            notify_kyc_status_changed(user=user, level='2', new_status='Rejected')

            return Response(
                {'detail': f'Level 2 credentials rejected for {user.email}.'},
                status=status.HTTP_200_OK
            )


class Level3CredentialApprovalView(APIView):
    """Approve or reject Level 3 credentials."""
    permission_classes = [IsAdminUser]

    def post(self, request, credential_id):
        credentials = get_object_or_404(Level3Credentials, id=credential_id)

        if credentials.status != 'Pending':
            return Response(
                {'detail': f'Credentials already processed. Status: {credentials.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = CredentialApprovalSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        action = serializer.validated_data['action']

        # Find the user associated with these credentials
        user = UserProfile.objects.filter(level3_credentials=credentials).first()
        if not user:
            return Response(
                {'detail': 'No user associated with these credentials.'},
                status=status.HTTP_404_NOT_FOUND
            )

        if action == 'approve':
            credentials.status = 'Approved'
            credentials.approved = True
            credentials.save()

            # Upgrade user to Level 3
            user.level = 'Level 3'
            user.transaction_limit = Decimal('50000000.00')
            user.save()
            notify_kyc_status_changed(user=user, level='3', new_status='Approved')

            return Response(
                {'detail': f'Level 3 credentials approved for {user.email}. Transaction limit increased to 50,000,000.'},
                status=status.HTTP_200_OK
            )
        else:
            credentials.status = 'Rejected'
            credentials.approved = False
            credentials.save()
            notify_kyc_status_changed(user=user, level='3', new_status='Rejected')

            return Response(
                {'detail': f'Level 3 credentials rejected for {user.email}.'},
                status=status.HTTP_200_OK
            )


class PendingOrdersListView(ListAPIView):
    """List all pending gift card orders."""
    permission_classes = [IsAdminUser]
    serializer_class = PendingOrderSerializer

    def get_queryset(self):
        return GiftCardOrder.objects.filter(status='Pending')


class OrderStatusUpdateView(APIView):
    """Update the status of an order. Balance updates are handled automatically by signals."""
    permission_classes = [IsAdminUser]
    serializer_class = OrderStatusUpdateSerializer

    def patch(self, request, order_id):
        order = get_object_or_404(GiftCardOrder, id=order_id)
        old_status = order.status

        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        new_status = serializer.validated_data['status']
        admin_notes = serializer.validated_data.get('admin_notes', '')

        order.status = new_status
        if admin_notes:
            # Store admin notes if you add the field to the model
            pass
        order.save()
        order.user.refresh_from_db(fields=['pending_balance', 'withdrawable_balance'])

        # Notify balance update
        if new_status in ['Approved', 'Completed']:
            balance_type = 'withdrawable'
            new_balance = float(order.user.withdrawable_balance)
            change_amount = float(order.amount)
        else:
            balance_type = 'pending'
            new_balance = float(order.user.pending_balance)
            change_amount = None

        notify_balance_updated(
            user=order.user,
            balance_type=balance_type,
            new_balance=new_balance,
            change_amount=change_amount,
        )

        return Response(
            {'detail': f'Order status updated from {old_status} to {order.status}.'},
            status=status.HTTP_200_OK
        )


# Withdrawal Admin Views

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
                transaction_reference=transaction_reference,
            )
            withdrawal.user.refresh_from_db(fields=['withdrawable_balance'])

            return Response({
                'detail': f'Withdrawal approved successfully. The requested amount ${withdrawal.amount} remains deducted from user\'s withdrawable balance.',
                'status': withdrawal.status,
                'transaction_reference': withdrawal.transaction_reference,
                'withdrawable_balance': str(withdrawal.user.withdrawable_balance),
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
                reason=reason,
            )
            withdrawal.user.refresh_from_db(fields=['withdrawable_balance'])

            return Response({
                'detail': f'Withdrawal rejected. Amount ${withdrawal.amount} has been returned to user withdrawable balance. Reason: {reason}',
                'status': withdrawal.status,
                'withdrawable_balance': str(withdrawal.user.withdrawable_balance),
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

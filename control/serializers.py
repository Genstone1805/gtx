from rest_framework import serializers
from decimal import Decimal
from cards.models import GiftCardNames, GiftCardStore
from account.models import Level2Credentials, Level3Credentials, UserProfile
from order.models import GiftCardOrder
from withdrawal.models import Withdrawal, WithdrawalAuditLog

class CreateGiftStoreSerializer(serializers.ModelSerializer):
  image = serializers.ImageField(use_url=False)
  cards = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False,
    )
  
  class Meta:
    model = GiftCardStore
    fields = ["category", "name", "image", "cards"]

class UpdateGiftStoreSerializer(serializers.ModelSerializer):
  image = serializers.ImageField(use_url=False, required=False)
  class Meta:
    model = GiftCardStore
    fields = ["category", "name", "image"]

class GiftStoreListSerializer(serializers.ModelSerializer):
  class Meta:
    model = GiftCardStore
    fields = ["id", "name"]

class GiftCardListSerializer(serializers.ModelSerializer):
  store = GiftStoreListSerializer(read_only=True)
  class Meta:
    model = GiftCardNames
    fields = ["id", "name", "rate", "type", "store" ]

class CreateGiftCardSerializer(serializers.ModelSerializer):
  class Meta:
    model = GiftCardNames
    fields = ["type", "name", "store", "rate"]


class UserBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['id', 'email', 'full_name', 'phone_number', 'level', 'transaction_limit']


class Level2CredentialsPendingSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = Level2Credentials
        fields = ['id', 'nin', 'nin_image', 'status', 'approved', 'user']

    def get_user(self, obj):
        user = UserProfile.objects.filter(level2_credentials=obj).first()
        if user:
            return UserBasicSerializer(user).data
        return None


class Level3CredentialsPendingSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = Level3Credentials
        fields = [
            'id', 'house_address_1', 'house_address_2', 'nearest_bus_stop',
            'city', 'state', 'country', 'proof_of_address_image',
            'face_verification_image', 'status', 'approved', 'user'
        ]

    def get_user(self, obj):
        user = UserProfile.objects.filter(level3_credentials=obj).first()
        if user:
            return UserBasicSerializer(user).data
        return None


class CredentialApprovalSerializer(serializers.Serializer):
    ACTION_CHOICES = [
        ('approve', 'Approve'),
        ('reject', 'Reject'),
    ]
    action = serializers.ChoiceField(choices=ACTION_CHOICES)
    reason = serializers.CharField(required=False, allow_blank=True)


class PendingOrderSerializer(serializers.ModelSerializer):
    user = UserBasicSerializer(read_only=True)

    class Meta:
        model = GiftCardOrder
        fields = ['id', 'type', 'card', 'image', 'e_code_pin', 'amount', 'status', 'user']


class OrderStatusUpdateSerializer(serializers.Serializer):
    STATUS_CHOICES = [
        ('Processing', 'Processing'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Assigned', 'Assigned'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]
    status = serializers.ChoiceField(choices=STATUS_CHOICES)
    admin_notes = serializers.CharField(required=False, allow_blank=True)


# Withdrawal Admin Serializers

class WithdrawalListSerializer(serializers.ModelSerializer):
    """Serializer for listing withdrawals."""
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Withdrawal
        fields = [
            'id', 'amount',
            'status', 'status_display', 'created_at', 'updated_at'
        ]


class WithdrawalDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed withdrawal view."""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_full_name = serializers.CharField(source='user.full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Withdrawal
        fields = [
            'id', 'user', 'user_email', 'user_full_name',
            'amount',
            'bank_name', 'account_name', 'account_number',
            'status', 'status_display',
            'processed_by', 'processed_at', 'rejection_reason', 'admin_notes',
            'transaction_reference',
            'created_at', 'updated_at'
        ]


class WithdrawalApprovalSerializer(serializers.Serializer):
    """Serializer for admin to approve/reject withdrawal."""
    ACTION_CHOICES = [
        ('approve', 'Approve'),
        ('reject', 'Reject'),
    ]
    action = serializers.ChoiceField(choices=ACTION_CHOICES, required=True)
    reason = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    transaction_reference = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    admin_notes = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate(self, data):
        action = data.get('action')
        reason = data.get('reason')

        if action == 'reject' and not reason:
            raise serializers.ValidationError({
                'reason': 'A rejection reason is required when rejecting a withdrawal.'
            })

        return data


class WithdrawalAuditLogSerializer(serializers.ModelSerializer):
    """Serializer for withdrawal audit logs."""
    performed_by_email = serializers.EmailField(source='performed_by.email', read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)

    class Meta:
        model = WithdrawalAuditLog
        fields = [
            'id', 'withdrawal', 'action', 'action_display',
            'performed_by', 'performed_by_email',
            'details', 'previous_status', 'new_status',
            'created_at'
        ]
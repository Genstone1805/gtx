from rest_framework import serializers
from decimal import Decimal
from .models import Withdrawal
from account.models import UserProfile


class WithdrawalCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a withdrawal request."""

    class Meta:
        model = Withdrawal
        fields = [
            'id', 'amount',
            'bank_name', 'account_name', 'account_number',
        ]

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")

        # Check if user has sufficient withdrawable balance
        user = self.context['request'].user
        if value > user.withdrawable_balance:
            raise serializers.ValidationError(
                f"Insufficient withdrawable balance. Your current withdrawable balance is ₦{user.withdrawable_balance:,.2f}."
            )

        return value

    def validate(self, data):
        # Auto-fill missing bank details from user's saved bank details.
        user = self.context['request'].user
        saved_bank_details = getattr(user, 'bank_details', None)
        if saved_bank_details:
            data.setdefault('bank_name', saved_bank_details.bank_name)
            data.setdefault('account_name', saved_bank_details.account_name)
            data.setdefault('account_number', saved_bank_details.account_number)

        # Validate required bank details
        required_fields = ['bank_name', 'account_name', 'account_number']
        missing_fields = [f for f in required_fields if not data.get(f)]
        if missing_fields:
            raise serializers.ValidationError({
                f: f"This field is required."
                for f in missing_fields
            })

        return data

    def create(self, validated_data):
        request = self.context['request']
        validated_data['user'] = request.user
        return super().create(validated_data)


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


class UserBalanceSerializer(serializers.Serializer):
    """Serializer for user balance information."""
    pending_balance = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    withdrawable_balance = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    transaction_limit = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_balance = serializers.SerializerMethodField()

    def get_total_balance(self, obj):
        # obj is the user profile
        return obj.pending_balance + obj.withdrawable_balance

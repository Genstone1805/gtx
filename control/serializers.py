from rest_framework import serializers
from cards.models import GiftCardNames, GiftCardStore
from account.models import Level2Credentials, Level3Credentials, UserProfile
from order.models import GiftCardOrder

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
    ]
    status = serializers.ChoiceField(choices=STATUS_CHOICES)
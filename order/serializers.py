from rest_framework import serializers
from .models import GiftCardOrder


class GiftCardOrderListSerializer(serializers.ModelSerializer):
    class Meta:
        model = GiftCardOrder
        fields = ["id", 'type', 'card', 'image', 'amount', 'e_code_pin', 'status']


class GiftCardOrderCreateSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False, allow_null=True)
    e_code_pin = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = GiftCardOrder
        fields = ["id", 'type', 'card', 'image', 'amount', "e_code_pin"]

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value

    def validate(self, data):
        card_type = data.get('type')

        if card_type == 'E-Code' and not data.get('e_code_pin'):
            raise serializers.ValidationError({'e_code_pin': 'Pin is required for ecode type.'})

        if card_type == 'Physical' and not data.get('image'):
            raise serializers.ValidationError({'image': 'Image is required for physical type.'})

        return data

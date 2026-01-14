from rest_framework import serializers
from .models import GiftCardOrder


class GiftCardOrderCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = GiftCardOrder
        fields = ["id", 'type', 'card', 'image', 'amount', "e_code_pin"]

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value

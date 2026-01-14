from rest_framework import serializers
from .models import GiftCardOrder


class GiftCardOrderCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = GiftCardOrder
        fields = ['type', 'name', 'image', 'amount']

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value

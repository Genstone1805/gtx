from rest_framework import serializers
from .models import GiftCardOrder
from cards.models import GiftCardNames, GiftCardStore


class GiftCardStoreSerializer(serializers.ModelSerializer):
  image = serializers.ImageField(use_url=True)
  class Meta:
    model = GiftCardStore
    fields = ["name", "image"]


class GiftCardNameListSerializer(serializers.ModelSerializer):
  store = GiftCardStoreSerializer(read_only=True)
  class Meta:
    model = GiftCardNames
    fields = ["name", "store"]

class GiftCardNameSerializer(serializers.ModelSerializer):
  store = GiftCardStoreSerializer(read_only=True)
  class Meta:
    model = GiftCardNames
    fields = ["id", "name", "type", "rate", "store"]

class GiftCardOrderSerializer(serializers.ModelSerializer):
    card = GiftCardNameSerializer()
    class Meta:
        model = GiftCardOrder
        fields = ["id", 'type', 'card', 'image', 'amount', 'e_code_pin', 'status']
class GiftCardOrderListSerializer(serializers.ModelSerializer):
    card = GiftCardNameListSerializer()
    class Meta:
        model = GiftCardOrder
        fields = ["id", 'card', 'amount', 'status']


class GiftCardOrderHistorySerializer(serializers.ModelSerializer):
    card = GiftCardNameListSerializer()

    class Meta:
        model = GiftCardOrder
        fields = ["id", "type", "card", "amount", "status", "created_at"]


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

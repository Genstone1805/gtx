from rest_framework import serializers
from cards.models import GiftCardNames, GiftCardStore
from cards.serializers import GiftCardNameSerializer




class CreateGiftStoreSerializer(serializers.ModelSerializer):
  image = serializers.ImageField(use_url=False)
  cards = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False,
    )
  
  class Meta:
    model = GiftCardStore
    fields = ["category", "name", "image", "rate", "cards"]
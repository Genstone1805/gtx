from rest_framework import serializers
from cards.models import GiftCardStore, GiftCardNames

class GiftCardNameSerializer(serializers.ModelSerializer):
  class Meta:
    model = GiftCardNames
    fields = ["store", "name", "rate", "type"]

class GiftCardStoreListSerializer(serializers.ModelSerializer):
  # cards = serializers.SerializerMethodField()
  image = serializers.ImageField(read_only=True)
  class Meta:
    model = GiftCardStore
    fields = ["category", "name", "image"]

  # def get_cards(self, obj):
  #   cards = GiftCardNames.objects.filter(store=obj)
  #   return GiftCardNameSerializer(cards, many=True).data

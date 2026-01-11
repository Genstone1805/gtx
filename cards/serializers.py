from rest_framework import serializers
from cards.models import GiftCardStore, GiftCardNames

class GiftCardNameSerializer(serializers.ModelSerializer):
  class Meta:
    model = GiftCardNames
    fields = ["name", "type", "rate"]

class GiftCardStoreListSerializer(serializers.ModelSerializer):
  cards = serializers.SerializerMethodField()
  image = serializers.ImageField(use_url=True)
  class Meta:
    model = GiftCardStore
    fields = ["category", "name", "image", "cards"]

  def get_cards(self, obj):
    cards = GiftCardNames.objects.filter(store=obj)
    return GiftCardNameSerializer(cards, many=True).data

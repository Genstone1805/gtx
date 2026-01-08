from rest_framework import serializers
from cards.models import GiftCardStore, GiftCardNames


class GiftCardStoreListSerializer(serializers.ModelSerializer):
  cards = serializers.SerializerMethodField()
  class Meta:
    model = GiftCardStore
    fields = ["category", "name", "image", "rate", "cards"]

  def get_cards(self, obj):
    cards = GiftCardNames.objects.filter(store=obj)
    return cards

class GiftCardNameSerializer(serializers.ModelSerializer):
  class Meta:
    model = GiftCardNames
    fields = ["store", "name"]
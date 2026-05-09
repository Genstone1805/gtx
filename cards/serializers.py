from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from cards.models import GiftCardStore, GiftCardNames

class GiftCardNameSerializer(serializers.ModelSerializer):
  rate = serializers.DecimalField(max_digits=12, decimal_places=2)

  class Meta:
    model = GiftCardNames
    fields = ["id", "name", "type", "rate"]
    ref_name = "CardsGiftCardName"

class GiftCardStoreListSerializer(serializers.ModelSerializer):
  cards = serializers.SerializerMethodField()
  image = serializers.ImageField(use_url=True)
  class Meta:
    model = GiftCardStore
    fields = ["id", "category", "name", "image", "cards"]

  @extend_schema_field(GiftCardNameSerializer(many=True))
  def get_cards(self, obj) -> list[dict]:
    cards = GiftCardNames.objects.filter(store=obj)
    return GiftCardNameSerializer(cards, many=True).data

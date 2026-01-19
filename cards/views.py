from rest_framework.generics import ListAPIView
from cards.models import GiftCardStore
from .serializers import GiftCardStoreListSerializer



class GiftCardStoreListView(ListAPIView):
  serializer_class = GiftCardStoreListSerializer
  queryset = GiftCardStore.objects.all()
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from cards.models import GiftCardStore, GiftCardNames
from .serializers import GiftCardStoreListSerializer, GiftCardNameSerializer


class GiftCardStoreListView(ListAPIView):
    serializer_class = GiftCardStoreListSerializer
    queryset = GiftCardStore.objects.all()


class GiftCardListView(ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = GiftCardNameSerializer
    queryset = GiftCardNames.objects.all()
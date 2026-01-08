from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework import status
from cards.models import GiftCardStore
from .serializers import GiftCardStoreListSerializer



class GiftCardStoreListView(ListAPIView):
  serializer_class = GiftCardStoreListSerializer
  queryset = GiftCardStore.objects.all()
  
  def get_serializer_context(self):
    context = super().get_serializer_context()
    context["request"] = self.request
    return context
  


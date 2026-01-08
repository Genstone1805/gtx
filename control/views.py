from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework import status
from cards.models import GiftCardStore
from .serializers import CreateGiftStoreSerializer


class CreateGiftStoreView(APIView):
  serializer_class = CreateGiftStoreSerializer

  def post(self, request, *args, **kwargs):
    # user = request.user
    data = request.data
    serializer = self.serializer_class(data = data)
    try:
      serializer.is_valid(raise_exception=True)
      cards = serializer.data.pop("cards", [])
      if cards:
        for card in cards:
          pass
      else:
        pass
      return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
      return Response(str(e), status=400)
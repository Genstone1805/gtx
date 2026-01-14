from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser

from .models import GiftCardOrder
from .serializers import GiftCardOrderCreateSerializer


class CreateGiftCardOrderView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    serializer_class = GiftCardOrderCreateSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        order = GiftCardOrder.objects.create(
            user=request.user,
            type=serializer.validated_data['type'],
            name=serializer.validated_data['name'],
            image=serializer.validated_data['image'],
            amount=serializer.validated_data['amount'],
        )

        return Response(
            {
                'detail': 'Order created successfully.',
            },
            status=status.HTTP_201_CREATED
        )

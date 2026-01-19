from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.views.generic import TemplateView

from .models import GiftCardOrder
from .serializers import GiftCardOrderCreateSerializer


class CreateOrderPageView(TemplateView):
    template_name = 'order/create_order.html'


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
            card=serializer.validated_data['card'],
            image=serializer.validated_data.get('image', None),
            e_code_pin=serializer.validated_data.get('e_code_pin', None),
            amount=serializer.validated_data['amount'],
        )

        return Response(
            {
                'detail': 'Order created successfully.',
            },
            status=status.HTTP_201_CREATED
        )

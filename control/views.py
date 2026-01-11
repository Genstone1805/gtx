import json
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAdminUser
from django.shortcuts import get_object_or_404
from decimal import Decimal

from cards.models import GiftCardStore, GiftCardNames
from account.models import Level2Credentials, Level3Credentials, UserProfile
from .serializers import (
   CreateGiftStoreSerializer,
   CreateGiftCardSerializer,
   GiftStoreListSerializer,
   GiftCardListSerializer,
   UpdateGiftStoreSerializer,
   Level2CredentialsPendingSerializer,
   Level3CredentialsPendingSerializer,
   CredentialApprovalSerializer
   )


def parse_querydict(query_dict):
    data = {}

    for key in query_dict.keys():
        value = query_dict.get(key)

        # Skip if value is a file upload (keep as-is)
        if hasattr(value, 'read'):
            data[key] = value
            continue

        # Try to parse as JSON (for arrays/objects passed as strings)
        if isinstance(value, str):
            stripped = value.strip()
            if stripped.startswith(('[', '{')):
                try:
                    data[key] = json.loads(stripped)
                    continue
                except json.JSONDecodeError:
                    pass

        # Default: use the value as-is (strip whitespace for strings)
        data[key] = value.strip() if isinstance(value, str) else value

    return data

class CreateGiftStoreView(APIView):
  serializer_class = CreateGiftStoreSerializer

  def post(self, request, *args, **kwargs):
    # user = request.user
    data = parse_querydict(request.data)
    serializer = self.serializer_class(data = data)
    try:
      serializer.is_valid(raise_exception=True)
      cards = serializer.validated_data.pop("cards", [])
      store = GiftCardStore.objects.create(**serializer.validated_data)
      if cards:
        for card in cards:
          GiftCardNames.objects.create(store=store, **card)
      return Response("Store Created", status=status.HTTP_200_OK)
    except Exception as e:
      return Response(str(e), status=400)

class GiftCardListView(ListAPIView):
  serializer_class = GiftCardListSerializer
  queryset = GiftCardNames.objects.all()

class GiftStoreListView(ListAPIView):
  serializer_class = GiftStoreListSerializer
  queryset = GiftCardStore.objects.all()

class CreateGiftCardView(APIView):
  serializer_class = CreateGiftCardSerializer

  def post(self, request, *args, **kwargs):
    data = request.data
    serializer = self.serializer_class(data = data)
    
    try:
      serializer.is_valid(raise_exception=True)
      GiftCardNames.objects.create(**serializer.validated_data)
      return Response("Gift Card Created", status=status.HTTP_200_OK)
    except Exception as e:
      return Response(str(e), status=400)
    
class GiftCardRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
  serializer_class = CreateGiftCardSerializer
  lookup_field = "pk"
  queryset = GiftCardNames.objects.all()
    
class GiftStoreRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
  serializer_class = UpdateGiftStoreSerializer
  lookup_field = "pk"
  queryset = GiftCardStore.objects.all()


class PendingLevel2CredentialsListView(ListAPIView):
    """List all pending Level 2 credential submissions."""
    permission_classes = [IsAdminUser]
    serializer_class = Level2CredentialsPendingSerializer

    def get_queryset(self):
        return Level2Credentials.objects.filter(status='Pending')


class PendingLevel3CredentialsListView(ListAPIView):
    """List all pending Level 3 credential submissions."""
    permission_classes = [IsAdminUser]
    serializer_class = Level3CredentialsPendingSerializer

    def get_queryset(self):
        return Level3Credentials.objects.filter(status='Pending')


class Level2CredentialApprovalView(APIView):
    """Approve or reject Level 2 credentials."""
    permission_classes = [IsAdminUser]

    def post(self, request, credential_id):
        credentials = get_object_or_404(Level2Credentials, id=credential_id)

        if credentials.status != 'Pending':
            return Response(
                {'detail': f'Credentials already processed. Status: {credentials.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = CredentialApprovalSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        action = serializer.validated_data['action']

        # Find the user associated with these credentials
        user = UserProfile.objects.filter(level2_credentials=credentials).first()
        if not user:
            return Response(
                {'detail': 'No user associated with these credentials.'},
                status=status.HTTP_404_NOT_FOUND
            )

        if action == 'approve':
            credentials.status = 'Approved'
            credentials.approved = True
            credentials.save()

            # Upgrade user to Level 2
            user.level = 'Level 2'
            user.transaction_limit = Decimal('5000000.00')
            user.save()

            return Response(
                {'detail': f'Level 2 credentials approved for {user.email}. Transaction limit increased to 5,000,000.'},
                status=status.HTTP_200_OK
            )
        else:
            credentials.status = 'Rejected'
            credentials.approved = False
            credentials.save()

            return Response(
                {'detail': f'Level 2 credentials rejected for {user.email}.'},
                status=status.HTTP_200_OK
            )


class Level3CredentialApprovalView(APIView):
    """Approve or reject Level 3 credentials."""
    permission_classes = [IsAdminUser]

    def post(self, request, credential_id):
        credentials = get_object_or_404(Level3Credentials, id=credential_id)

        if credentials.status != 'Pending':
            return Response(
                {'detail': f'Credentials already processed. Status: {credentials.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = CredentialApprovalSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        action = serializer.validated_data['action']

        # Find the user associated with these credentials
        user = UserProfile.objects.filter(level3_credentials=credentials).first()
        if not user:
            return Response(
                {'detail': 'No user associated with these credentials.'},
                status=status.HTTP_404_NOT_FOUND
            )

        if action == 'approve':
            credentials.status = 'Approved'
            credentials.approved = True
            credentials.save()

            # Upgrade user to Level 3
            user.level = 'Level 3'
            user.transaction_limit = Decimal('50000000.00')
            user.save()

            return Response(
                {'detail': f'Level 3 credentials approved for {user.email}. Transaction limit increased to 50,000,000.'},
                status=status.HTTP_200_OK
            )
        else:
            credentials.status = 'Rejected'
            credentials.approved = False
            credentials.save()

            return Response(
                {'detail': f'Level 3 credentials rejected for {user.email}.'},
                status=status.HTTP_200_OK
            )
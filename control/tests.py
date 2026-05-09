from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from cards.models import GiftCardNames, GiftCardStore
from control.serializers import CreateGiftStoreSerializer, GiftCardListSerializer


class GiftCardRateTests(TestCase):
    def test_list_serializer_handles_rates_above_old_six_digit_limit(self):
        store = GiftCardStore.objects.create(name="Apple", category="Popular")
        card = GiftCardNames.objects.create(
            store=store,
            name="Apple US",
            type="E-code",
            rate=Decimal("25000.00"),
        )

        data = GiftCardListSerializer(card).data

        self.assertEqual(data["rate"], "25000.00")

    def test_nested_store_cards_validate_decimal_limits(self):
        serializer = CreateGiftStoreSerializer(
            data={
                "category": "Popular",
                "name": "Steam",
                "cards": [
                    {
                        "name": "Steam US",
                        "type": "E-code",
                        "rate": "10000000000.00",
                    }
                ],
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("cards", serializer.errors)
        self.assertIn("rate", serializer.errors["cards"][0])

    def test_rate_cannot_be_negative(self):
        store = GiftCardStore.objects.create(name="Amazon", category="Shopping")
        card = GiftCardNames(
            store=store,
            name="Amazon US",
            type="Physical",
            rate=Decimal("-1.00"),
        )

        with self.assertRaises(ValidationError):
            card.full_clean()

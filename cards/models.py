from django.db import models
from django.contrib.auth import get_user_model
from decimal import Decimal

user = get_user_model()

class GiftCardStore(models.Model):
  CATEGORY_CHOICES = [
    ("All", "All"),
    ("Popular", "Popular"),
    ("Shopping", "Shopping"),

  ]
  category = models.CharField(choices=CATEGORY_CHOICES, max_length=50, default="All")
  name = models.CharField(max_length=50, unique=True)
  image = models.ImageField(upload_to="gift stores", null=True)

  user = models.ForeignKey(user, on_delete=models.CASCADE, related_name="gift_card_store_creator", null=True)

  def __str__(self) -> str:
    return self.name


class GiftCardNames(models.Model):
  TYPE_CHOICES = [
    ("Both", "Both"),
    ("Physical", "Physical"),
    ("E-ncode", "E-ncode"),

  ]
  type = models.CharField(choices=TYPE_CHOICES, max_length=50, default="Both")
  name = models.CharField(max_length=150)
  store = models.ForeignKey(GiftCardStore, on_delete=models.CASCADE)
  user = models.ForeignKey(user, on_delete=models.CASCADE, related_name="gift_card_name_creator", null=True)
  rate = models.DecimalField(decimal_places=2, max_digits=6, default=Decimal("0.00"))

  def __str__(self) -> str:
    return self.name



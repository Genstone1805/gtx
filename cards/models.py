from django.db import models
from django.contrib.auth import get_user_model

user = get_user_model()

class GiftCardStore(models.Model):
  CATEGORY_CHOICES = [
    ("All", "All"),
    ("Popular", "Popular"),
    ("Shopping", "Shopping"),

  ]
  category = models.CharField(choices=CATEGORY_CHOICES, max_length=50, default="All")
  name = models.CharField(max_length=50, unique=True)
  image = models.ImageField()
  user = models.ForeignKey(user, on_delete=models.CASCADE, related_name="gift_card_store_creator", null=True)
  rate = models.FloatField()


class GiftCardNames(models.Model):
  name = models.CharField(max_length=150, unique=True)
  store = models.ForeignKey(GiftCardStore, on_delete=models.CASCADE)
  user = models.ForeignKey(user, on_delete=models.CASCADE, related_name="gift_card_name_creator", null=True)



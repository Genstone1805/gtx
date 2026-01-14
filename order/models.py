from django.db import models
from cards.models import GiftCardNames
from django.contrib.auth import get_user_model

user = get_user_model()

class GiftCardOrder(models.Model):
  TYPE_CHOICES = [
    ("Physical", "Physical"),
    ("E-Code", "E-Code"),
  ]

  STATUS_CHOICES = [
    ("Processing", "Processing"),
    ("Rejected", "Rejected"),
    ("Approved", "Approved"),
  ]

  user = models.ForeignKey(user, on_delete=models.CASCADE)
  type = models.CharField(choices=TYPE_CHOICES, max_length=50)
  name = models.ForeignKey(GiftCardNames, on_delete=models.SET_NULL, null=True)
  image = models.ImageField(upload_to="orders/")
  amount = models.IntegerField()
  status = models.CharField(choices=STATUS_CHOICES, max_length=50, default="Processing")

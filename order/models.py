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
    ("Pending", "Pending"),
    ("Approved", "Approved"),
    ("Rejected", "Rejected"),
  ]

  user = models.ForeignKey(user, on_delete=models.CASCADE)
  type = models.CharField(choices=TYPE_CHOICES, max_length=50)
  card = models.ForeignKey(GiftCardNames, on_delete=models.SET_NULL, null=True)
  image = models.ImageField(upload_to="orders/", null=True, blank=True)
  e_code_pin = models.CharField(max_length=25, null=True, blank=True)
  amount = models.IntegerField()
  status = models.CharField(choices=STATUS_CHOICES, max_length=50, default="Pending")
  created_at = models.DateTimeField(auto_now_add=True, null=True)

  def __str__(self):
    return f"Order #{self.id} - {self.user.email} - ${self.amount}"

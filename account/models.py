from django.db import models
from authemail.models import EmailUserManager, EmailAbstractUser
from phonenumber_field.modelfields import PhoneNumberField
from django.utils import timezone



class Level2Credentials(models.Model):
    STATUS = [
        ("Pending", "Pending"),
        ("Approved", "Approved"),
        ("Rejected", "Rejected"),    
    ]

    nin = models.CharField(max_length=12, blank=True, unique=True)
    nin_image = models.ImageField()
    status = models.CharField(choices=STATUS, default="Level 1", max_length=12)
    approved = models.BooleanField(default=False)



class Level3Credentials(models.Model):
    STATUS = [
        ("Pending", "Pending"),
        ("Approved", "Approved"),
        ("Rejected", "Rejected"),
    ]
    
    house_address_1 = models.CharField(max_length=100)
    house_address_2 = models.CharField(max_length=100, blank=True)
    nearest_bus_stop = models.TextField(max_length=60)
    city = models.TextField(max_length=50)
    state = models.CharField(max_length=50)
    country = models.CharField(max_length=50)
    proof_of_address_image = models.ImageField()
    face_verification_image = models.ImageField()
    status = models.CharField(choices=STATUS, default="Level 1", max_length=12)
    approved = models.BooleanField(default=False)


class UserProfile(EmailAbstractUser):
  STATUS = [
    ("Active", "Active"),
    ("Warning", "Warning"),
    ("Disabled", "Disabled"),
    ("Under Review", "Under Review"),
  ]

  LEVEL_CHOICES = [
    ("Level 1", "Level 1"),
    ("Level 2", "Level 2"),
    ("Level 3", "Level 3"),
  ]

	# Custom fields
  dp = models.ImageField(blank=True)
  full_name = models.CharField(max_length=80)
  phone_number = PhoneNumberField(unique=True, blank=True, null=True)
  # username = models.CharField(verbose_name='Username', default="", max_length=50, unique=True, blank=True, null=True)
  # email = models.EmailField(verbose_name='Email', max_length=100, unique=True)
  level = models.CharField(choices=LEVEL_CHOICES, default="Level 1", max_length=12)
  level2_credentialas = models.ForeignKey(Level2Credentials, on_delete=models.SET_NULL, null=True, blank=True)
  level3_credentials = models.ForeignKey(Level3Credentials, on_delete=models.SET_NULL, null=True, blank=True)
  transaction_pin = models.CharField(max_length=4, blank=True)
  status = models.CharField(choices=STATUS, default="Active", max_length=12)
  disabled = models.BooleanField(default=False)
  ip_address = models.GenericIPAddressField(null=True, blank=True)
  created_at = models.DateTimeField(auto_now_add=True)
  last_login = models.DateTimeField(null=True, blank=True)

	# Required
  objects = EmailUserManager()
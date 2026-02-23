from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.auth.hashers import make_password, check_password
from phonenumber_field.modelfields import PhoneNumberField
from django.utils import timezone
from django.conf import settings
from decimal import Decimal
import random


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_verified', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, password, **extra_fields)



class Level2Credentials(models.Model):
    STATUS = [
        ("Pending", "Pending"),
        ("Approved", "Approved"),
        ("Rejected", "Rejected"),
    ]

    nin = models.CharField(max_length=12, blank=True, unique=True)
    nin_image = models.ImageField()
    status = models.CharField(choices=STATUS, default="Pending", max_length=12)
    approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return f"NIN: {self.nin}"


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
    status = models.CharField(choices=STATUS, default="Pending", max_length=12)
    approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return f"Address: {self.house_address_1}"


class BankAccountDetails(models.Model):
    bank_name = models.CharField(max_length=100)
    account_number = models.CharField(max_length=20)
    account_name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return f"{self.bank_name} - {self.account_number}"


class UserProfile(AbstractBaseUser, PermissionsMixin):
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

    # Required fields for AbstractBaseUser
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    # Custom fields
    dp = models.ImageField(blank=True)
    full_name = models.CharField(max_length=80, blank=True)
    phone_number = PhoneNumberField(unique=True, blank=True, null=True)
    bank_details = models.ForeignKey(
        BankAccountDetails,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users_bank_details'
    )
    level = models.CharField(choices=LEVEL_CHOICES, default="Level 1", max_length=12)
    level2_credentials = models.ForeignKey(Level2Credentials, on_delete=models.SET_NULL, null=True, blank=True)
    level3_credentials = models.ForeignKey(Level3Credentials, on_delete=models.SET_NULL, null=True, blank=True)
    transaction_pin = models.CharField(max_length=128, blank=True)
    has_pin = models.BooleanField(default=False)
    transaction_limit = models.DecimalField(decimal_places=2, max_digits=12, default=Decimal("250000.00"))
    
    # Balance fields for gift card redemption system
    pending_balance = models.DecimalField(decimal_places=2, max_digits=12, default=Decimal("0.00"),
        help_text="Total amount from orders with 'Pending' status (awaiting admin approval)"
    )
    withdrawable_balance = models.DecimalField(decimal_places=2, max_digits=12, default=Decimal("0.00"),
        help_text="Total amount from orders with 'Approved' status (available for withdrawal)"
    )
    
    status = models.CharField(choices=STATUS, default="Active", max_length=12)
    disabled = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    
    def set_transaction_pin(self, raw_pin):
        self.transaction_pin = make_password(raw_pin)
        self.has_pin = True

    def check_transaction_pin(self, raw_pin):
        return check_password(raw_pin, self.transaction_pin)

    def __str__(self):
        return self.email


class EmailVerificationCode(models.Model):
    """Stores 6-digit verification codes for email verification."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='verification_codes'
    )
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    @classmethod
    def generate_code(cls):
        """Generate a random 6-digit code."""
        return str(random.randint(100000, 999999))

    @classmethod
    def create_for_user(cls, user):
        """Create a new verification code for a user, removing any existing ones."""
        cls.objects.filter(user=user).delete()
        code = cls.generate_code()
        return cls.objects.create(user=user, code=code)

    def is_expired(self):
        """Check if code is expired (valid for 10 minutes)."""
        from datetime import timedelta
        expiry_time = self.created_at + timedelta(minutes=10)
        return timezone.now() > expiry_time

    def __str__(self):
        return f"Code for {self.user.email}"


class PasswordResetCode(models.Model):
    """Stores 6-digit codes for password reset."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='password_reset_codes'
    )
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    @classmethod
    def generate_code(cls):
        """Generate a random 6-digit code."""
        return str(random.randint(100000, 999999))

    @classmethod
    def create_for_user(cls, user):
        """Create a new reset code for a user, removing any existing ones."""
        cls.objects.filter(user=user).delete()
        code = cls.generate_code()
        return cls.objects.create(user=user, code=code)

    def is_expired(self):
        """Check if code is expired (valid for 10 minutes)."""
        from datetime import timedelta
        expiry_time = self.created_at + timedelta(minutes=10)
        return timezone.now() > expiry_time

    def __str__(self):
        return f"Password reset code for {self.user.email}"

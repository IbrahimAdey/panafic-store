from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'merchant')
        extra_fields.setdefault('country', 'NG')
        extra_fields.setdefault('base_currency', 'NGN')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True, max_length=255)

    ROLE_CHOICES = [('merchant', 'Merchant'), ('customer', 'Customer')]
    COUNTRY_CHOICES = [('NG', 'Nigeria'), ('GH', 'Ghana'), ('KE', 'Kenya'), ('ZA', 'South Africa')]
    CURRENCY_CHOICES = [('NGN', 'NGN'), ('GHS', 'GHS'), ('KES', 'KES'), ('ZAR', 'ZAR')]

    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    country = models.CharField(max_length=2, choices=COUNTRY_CHOICES)
    base_currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES)

    full_name = models.CharField(max_length=255)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name', 'role', 'country', 'base_currency']

    objects = UserManager()

    def __str__(self):
        return f"{self.email} ({self.role})"

class RateCache(models.Model):
    base_currency = models.CharField(max_length=3)
    rates = models.JSONField()          # e.g. {"GHS": 0.047, "KES": 5.2, ...}
    fetched_at = models.DateTimeField()
    stale = models.BooleanField(default=False)

    class Meta:
        get_latest_by = 'fetched_at'
        app_label = 'core_legacy'  # Avoid clash with rates.RateCache

from django.db import models
from core.models import User
from products.models import Product

class Order(models.Model):
    STATUS_CHOICES = [('pending', 'Pending'), ('completed', 'Completed'), ('review_required', 'Review Required')]
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='customer_orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    customer_currency = models.CharField(max_length=3)
    customer_total = models.DecimalField(max_digits=12, decimal_places=2)
    exchange_rate_applied = models.JSONField()  # full rates snapshot at checkout time
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'orders'

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    merchant = models.ForeignKey(User, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    unit_price_merchant_currency = models.DecimalField(max_digits=12, decimal_places=2)
    merchant_currency = models.CharField(max_length=3)
    merchant_payout_amount = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        app_label = 'orders'

class PayoutNotification(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    merchant = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3)
    status = models.CharField(max_length=10, choices=[('pending', 'Pending'), ('sent', 'Sent')], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'orders'

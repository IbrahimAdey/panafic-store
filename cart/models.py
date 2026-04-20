from django.db import models
from core.models import User
from products.models import Product

class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'cart'
        unique_together = ('user', 'product')  # prevent duplicate items

    def __str__(self):
        return f"{self.user.email} - {self.product.name} x{self.quantity}"

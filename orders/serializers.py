from rest_framework import serializers
from .models import Order, OrderItem

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['product', 'merchant', 'quantity', 'unit_price_merchant_currency',
                  'merchant_currency', 'merchant_payout_amount']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'status', 'customer_currency', 'customer_total',
                  'exchange_rate_applied', 'created_at', 'items']
from rest_framework import serializers
from .models import CartItem
from products.models import Product

class CartItemSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField(write_only=True, source='product.id')
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_currency = serializers.CharField(source='product.currency', read_only=True)
    unit_price = serializers.SerializerMethodField()
    line_total = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = [
            'id', 'product_id', 'product_name', 'product_currency',
            'quantity', 'unit_price', 'line_total', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def get_unit_price(self, obj):
        # Will be calculated in the view using customer's currency
        return None

    def get_line_total(self, obj):
        return None
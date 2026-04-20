from rest_framework import serializers
from .models import Product

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'currency', 'category', 'image_url', 'is_active', 'created_at']
        read_only_fields = ['merchant', 'currency']
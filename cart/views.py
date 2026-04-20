from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import CartItem
from .serializers import CartItemSerializer
from products.models import Product
from rates.services import RateService

class CartAddView(generics.CreateAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        if request.user.role != 'customer':
            return Response({"error": True, "message": "Only customers can add to cart"}, status=403)

        product_id = request.data.get('productId')
        quantity = request.data.get('quantity', 1)

        if not product_id:
            return Response({"error": True, "message": "productId is required"}, status=400)

        product = get_object_or_404(Product, id=product_id, is_active=True)

        # Add or update quantity
        cart_item, created = CartItem.objects.get_or_create(
            user=request.user,
            product=product,
            defaults={'quantity': quantity}
        )
        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        return Response({
            "error": False,
            "message": "Item added to cart",
            "cart_item_id": cart_item.id
        }, status=201)


class CartListView(generics.ListAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CartItem.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        data = serializer.data

        customer_currency = request.user.base_currency
        total = 0.0
        rates = RateService.get_cached_rates()
        stale = rates.get("stale", False)
        timestamp = rates.get("fetched_at")

        for item in data:
            product_currency = item['product_currency']
            price_in_merchant_currency = float(queryset.get(id=item['id']).product.price)

            try:
                converted_price = RateService.convert_price(
                    price_in_merchant_currency,
                    product_currency,
                    customer_currency
                )
                line_total = converted_price * item['quantity']
                item['unit_price'] = converted_price
                item['line_total'] = line_total
                total += line_total
            except:
                item['unit_price'] = None
                item['line_total'] = 0

        return Response({
            "error": False,
            "cart": data,
            "customer_currency": customer_currency,
            "total": round(total, 2),
            "rate_timestamp": timestamp,
            "stale": stale
        })


class CartRemoveView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, itemId, *args, **kwargs):
        if request.user.role != 'customer':
            return Response({"error": True, "message": "Only customers can modify cart"}, status=403)

        cart_item = get_object_or_404(CartItem, id=itemId, user=request.user)
        cart_item.delete()
        return Response({
            "error": False,
            "message": "Item removed from cart"
        }, status=200)

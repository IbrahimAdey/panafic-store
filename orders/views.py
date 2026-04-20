from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.throttling import UserRateThrottle
from cart.models import CartItem
from products.models import Product
from rates.services import RateService
from .models import Order, OrderItem, PayoutNotification
from .serializers import OrderSerializer


class CheckoutThrottle(UserRateThrottle):
    scope = 'checkout'
    rate = '5/min'   # exactly as per brief


class CheckoutView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [CheckoutThrottle]

    def post(self, request, *args, **kwargs):
        if request.user.role != 'customer':
            return Response({"error": True, "message": "Only customers can checkout"}, status=403)

        cart_items = CartItem.objects.filter(user=request.user)
        if not cart_items.exists():
            return Response({"error": True, "message": "Cart is empty"}, status=400)

        # 1. Lock the current rates (this is the critical part)
        locked_rates = RateService.get_cached_rates()
        customer_currency = request.user.base_currency

        # 2. Calculate totals
        customer_total = 0.0
        order_items_data = []

        for cart_item in cart_items:
            product = cart_item.product
            merchant_currency = product.currency
            merchant = product.merchant

            # Convert price to customer's currency
            converted_price = RateService.convert_price(
                float(product.price),
                merchant_currency,
                customer_currency
            )
            line_total = converted_price * cart_item.quantity
            customer_total += line_total

            # Merchant payout (customer_total * rate customer → merchant)
            merchant_rate = locked_rates[customer_currency][merchant_currency]
            merchant_payout = round(line_total * merchant_rate, 2)

            order_items_data.append({
                'product': product,
                'merchant': merchant,
                'quantity': cart_item.quantity,
                'unit_price_merchant_currency': product.price,
                'merchant_currency': merchant_currency,
                'merchant_payout_amount': merchant_payout
            })

        # 3. Create Order with locked rate
        order = Order.objects.create(
            customer=request.user,
            customer_currency=customer_currency,
            customer_total=round(customer_total, 2),
            exchange_rate_applied=locked_rates
        )

        # 4. Create OrderItems + PayoutNotifications
        for item_data in order_items_data:
            OrderItem.objects.create(order=order, **item_data)

            PayoutNotification.objects.create(
                order=order,
                merchant=item_data['merchant'],
                amount=item_data['merchant_payout_amount'],
                currency=item_data['merchant_currency']
            )

        # 5. Clear cart after successful checkout
        cart_items.delete()

        serializer = OrderSerializer(order)
        return Response({
            "error": False,
            "message": "Checkout successful - rate locked",
            "order": serializer.data
        }, status=201)


class OrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'merchant':
            # Merchant sees all orders where they are a seller
            return Order.objects.filter(items__merchant=user).distinct()
        else:
            # Customer sees their own orders
            return Order.objects.filter(customer=user)


class OrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'merchant':
            return Order.objects.filter(items__merchant=user).distinct()
        else:
            return Order.objects.filter(customer=user)

    def get_object(self):
        queryset = self.get_queryset()
        # Use full queryset (all orders) to distinguish between 404 and 403
        order = get_object_or_404(Order.objects.all(), id=self.kwargs['pk'])
        
        # Check if user has access
        if self.request.user.role == 'customer':
            if order.customer != self.request.user:
                raise permissions.exceptions.PermissionDenied("You do not have access to this order")
        elif self.request.user.role == 'merchant':
            if not order.items.filter(merchant=self.request.user).exists():
                raise permissions.exceptions.PermissionDenied("You do not have access to this order")
        
        return order

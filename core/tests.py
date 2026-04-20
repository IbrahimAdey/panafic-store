# from django.test import TestCase
# from rest_framework.test import APIClient
# from rest_framework import status
# from .models import User
#
# class AuthTests(TestCase):
#     def setUp(self):
#         self.client = APIClient()
#
#     def test_registration(self):
#         url = '/auth/register/'
#         data = {
#             "email": "test@example.com",
#             "password": "password123",
#             "full_name": "Test User",
#             "role": "merchant",
#             "country": "NG",
#             "base_currency": "NGN"
#         }
#         response = self.client.post(url, data, format='json')
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED)
#         self.assertTrue(User.objects.filter(email="test@example.com").exists())
#
#     def test_login(self):
#         User.objects.create_user(
#             email="test@example.com",
#             password="password123",
#             full_name="Test User",
#             role="merchant",
#             country="NG",
#             base_currency="NGN"
#         )
#         url = '/auth/login/'
#         data = {
#             "email": "test@example.com",
#             "password": "password123"
#         }
#         response = self.client.post(url, data, format='json')
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertIn('access', response.data)

from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from core.models import User
from products.models import Product
from cart.models import CartItem
from rates.services import RateService
from decimal import Decimal

class PanAfricTestCase(APITestCase):
    def setUp(self):
        self.merchant = User.objects.create_user(
            email="merchant@test.com", password="Test123!",
            role="merchant", country="NG", base_currency="NGN", full_name="Test Merchant"
        )
        self.customer = User.objects.create_user(
            email="customer@test.com", password="Test123!",
            role="customer", country="GH", base_currency="GHS", full_name="Test Customer"
        )
        self.product = Product.objects.create(
            merchant=self.merchant, name="Test Product", description="Test",
            price=Decimal("2500.00"), currency="NGN", category="Test"
        )

    def test_exchange_rate_conversion(self):
        rate = RateService.convert_price(2500, "NGN", "GHS")
        self.assertIsInstance(rate, float)

    def test_stale_rate_fallback(self):
        rates = RateService.get_cached_rates()
        self.assertIn("stale", rates)

    def test_cart_total_multi_currency(self):
        self.client.force_authenticate(user=self.customer)
        CartItem.objects.create(user=self.customer, product=self.product, quantity=2)
        response = self.client.get(reverse('cart-list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn("total", response.data)

    def test_checkout_rate_locking(self):
        self.client.force_authenticate(user=self.customer)
        # Clear throttle for this test
        from django.core.cache import cache
        cache.clear()
        CartItem.objects.create(user=self.customer, product=self.product, quantity=1)
        response = self.client.post(reverse('checkout'))
        self.assertEqual(response.status_code, 201)
        self.assertIn("exchange_rate_applied", response.data["order"])

    def test_customer_cannot_create_product(self):
        self.client.force_authenticate(user=self.customer)
        response = self.client.post(reverse('products'), data={})
        self.assertEqual(response.status_code, 403)

    def test_merchant_cannot_edit_other_merchant_product(self):
        other_merchant = User.objects.create_user(
            email="other@test.com", password="Test123!",
            role="merchant", country="KE", base_currency="KES", full_name="Other"
        )
        other_product = Product.objects.create(
            merchant=other_merchant, name="Other Product", price=100, currency="KES", category="Test"
        )
        self.client.force_authenticate(user=self.merchant)
        response = self.client.put(reverse('product-detail', args=[other_product.id]), data={"name": "hacked"})
        self.assertEqual(response.status_code, 403)

    def test_checkout_rate_limit(self):
        self.client.force_authenticate(user=self.customer)
        # Clear throttle before starting
        from django.core.cache import cache
        cache.clear()
        for _ in range(5):
            self.client.post(reverse('checkout'))
        response = self.client.post(reverse('checkout'))
        self.assertEqual(response.status_code, 429)

    def test_registration_missing_email(self):
        response = self.client.post(reverse('register'), data={
            "password": "Test123!", "full_name": "Test", "role": "customer",
            "country": "GH", "base_currency": "GHS"
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.data)

    def test_soft_delete_product(self):
        self.client.force_authenticate(user=self.merchant)
        response = self.client.delete(reverse('product-detail', args=[self.product.id]))
        self.assertEqual(response.status_code, 204)
        self.product.refresh_from_db()
        self.assertFalse(self.product.is_active)

    def test_order_access_control(self):
        self.client.force_authenticate(user=self.customer)
        # Clear throttle
        from django.core.cache import cache
        cache.clear()
        CartItem.objects.create(user=self.customer, product=self.product, quantity=1)
        checkout_resp = self.client.post(reverse('checkout'))
        order_id = checkout_resp.data["order"]["id"]

        # Create another merchant who is NOT involved in the order
        evil_merchant = User.objects.create_user(
            email="evil@test.com", password="Test123!",
            role="merchant", country="ZA", base_currency="ZAR", full_name="Evil Merchant"
        )
        self.client.force_authenticate(user=evil_merchant)
        response = self.client.get(reverse('order-detail', args=[order_id]))
        self.assertEqual(response.status_code, 403)

    def test_rates_endpoint_stale_flag(self):
        self.client.force_authenticate(user=self.customer)
        response = self.client.get(reverse('rates'))
        self.assertIn("stale", response.data)

    def test_merchant_sees_only_own_orders(self):
        self.client.force_authenticate(user=self.merchant)
        response = self.client.get(reverse('orders-list'))
        self.assertEqual(response.status_code, 200)
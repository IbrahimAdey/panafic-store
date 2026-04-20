from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from core.models import User
from .models import Product

class ProductTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.merchant = User.objects.create_user(
            email="merchant@example.com",
            password="password123",
            full_name="Merchant User",
            role="merchant",
            country="NG",
            base_currency="NGN"
        )
        self.client.force_authenticate(user=self.merchant)

    def test_create_product(self):
        url = '/products/'
        data = {
            "name": "Test Product",
            "description": "A test description",
            "price": "100.00",
            "category": "Electronics"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Product.objects.filter(name="Test Product").exists())

    def test_list_products(self):
        Product.objects.create(
            merchant=self.merchant,
            name="Test Product",
            description="A test description",
            price=100.00,
            currency="NGN",
            category="Electronics"
        )
        url = '/products/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['products']), 1)

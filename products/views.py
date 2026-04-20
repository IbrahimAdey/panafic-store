from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.db.models import Q
from .models import Product
from .serializers import ProductSerializer
from rates.services import RateService

class ProductListCreateView(generics.ListCreateAPIView):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True)
        search = self.request.query_params.get('search')
        category = self.request.query_params.get('category')
        country = self.request.query_params.get('country')

        if search:
            queryset = queryset.filter(Q(name__icontains=search) | Q(description__icontains=search))
        if category:
            queryset = queryset.filter(category__iexact=category)
        if country:
            queryset = queryset.filter(merchant__country__iexact=country)
        return queryset

    def perform_create(self, serializer):
        if self.request.user.role != 'merchant':
            raise permissions.exceptions.PermissionDenied("Only merchants can create products")
        serializer.save(merchant=self.request.user, currency=self.request.user.base_currency)

    def list(self, request, *args, **kwargs):
        currency = request.query_params.get('currency')
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        data = serializer.data

        if currency:
            rates = RateService.get_cached_rates()
            stale = rates.get('stale', False)
            for item in data:
                try:
                    converted = RateService.convert_price(float(item['price']), item['currency'], currency)
                    item['converted_price'] = converted
                    item['stale'] = stale
                except:
                    item['converted_price'] = None
                    item['stale'] = True

        return Response({"error": False, "products": data})

    def create(self, request, *args, **kwargs):
        if request.user.role != 'merchant':
            return Response({"error": True, "message": "Only merchants can create products"}, status=403)
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            product = serializer.save(merchant=request.user, currency=request.user.base_currency)
            return Response({
                "error": False,
                "message": "Product created successfully",
                "product": ProductSerializer(product).data
            }, status=201)
        return Response({"error": True, "message": "Validation error"}, status=400)


class ProductRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    queryset = Product.objects.filter(is_active=True)

    def get_object(self):
        obj = super().get_object()
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            if self.request.user.role != 'merchant' or obj.merchant != self.request.user:
                raise permissions.exceptions.PermissionDenied("You can only modify your own products")
        return obj

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data

        currency = request.query_params.get('currency')
        if currency:
            rates = RateService.get_cached_rates()
            stale = rates.get('stale', False)
            try:
                converted = RateService.convert_price(float(data['price']), data['currency'], currency)
                data['converted_price'] = converted
                data['stale'] = stale
            except:
                data['converted_price'] = None
                data['stale'] = True

        return Response({"error": False, "product": data})

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            self.perform_update(serializer)
            return Response({
                "error": False,
                "message": "Product updated successfully",
                "product": serializer.data
            })
        return Response({"error": True, "message": "Validation error"}, status=400)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({
            "error": False,
            "message": "Product deleted successfully"
        }, status=204)

    def perform_update(self, serializer):
        serializer.save()

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()

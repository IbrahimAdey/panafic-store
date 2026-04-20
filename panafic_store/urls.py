from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('core.urls')),
    path('api/core/', include('core.urls')),
    path('products/', include('products.urls')),
    path('rates/', include('rates.urls')),
    path('cart/', include('cart.urls')),
    path('orders/', include('orders.urls')),
]

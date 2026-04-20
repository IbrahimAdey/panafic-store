from django.urls import path
from .views import CartAddView, CartListView, CartRemoveView

urlpatterns = [
    path('', CartListView.as_view(), name='cart-list'),
    path('add/', CartAddView.as_view(), name='cart-add'),      # POST /cart/add/
    path('<int:itemId>/', CartRemoveView.as_view(), name='cart-remove'),
]
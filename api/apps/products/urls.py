from django.urls import path
from .views import ProductListAPI

urlpatterns = [
    path('', ProductListAPI.as_view(), name='product-list'),
]
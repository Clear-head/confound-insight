from rest_framework import generics
from .models import Product
from .serializers import ProductSerializer

class ProductListAPI(generics.ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
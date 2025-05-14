from rest_framework import generics
from store.models import ProductVariant
from .serializers import ProductStockSerializer

class ProductStockListAPIView(generics.ListAPIView):
    queryset = ProductVariant.objects.select_related('product').all()
    serializer_class = ProductStockSerializer

from rest_framework import serializers
from store.models import ProductVariant

class ProductStockSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField(source='product.id', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    sku = serializers.CharField(read_only=True)
    stock = serializers.IntegerField(read_only=True)

    class Meta:
        model = ProductVariant
        fields = ('product_id', 'product_name', 'sku', 'stock')

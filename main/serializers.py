# main/serializers.py
from rest_framework import serializers
from .models import Product, Order, OrderItem, Customer

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'description', 'image', 'category', 'stock'] [cite: 1391]

class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source='product.name')
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'quantity', 'price', 'subtotal'] [cite: 1394]

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'total_amount', 'address', 'phone', 'created_at', 
            'order_status', 'payment_method', 'payment_status', 'items'
        ] [cite: 1392]
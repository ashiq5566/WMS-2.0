from rest_framework import serializers
from inventory.models import Order, OrderItem, Product, Return, ReturnItem
from api.v1.accounts.serializers import StakeHolderSerializer
        
class OrderSerializer(serializers.ModelSerializer):
    stakeholder_obj = StakeHolderSerializer(source='stakeholder', read_only=True)

    class Meta:
        model = Order
        fields = '__all__'
        
class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'


product_obj = ProductSerializer(source='product', read_only=True)
class OrderItemSerializer(serializers.ModelSerializer):
    product_obj = ProductSerializer(source='product', read_only=True)
    class Meta:
        model = OrderItem
        fields = '__all__'
        
class ReturnSerializer(serializers.ModelSerializer):
    order_obj = OrderSerializer(source='original_order', read_only=True)
    class Meta:
        model = Return
        fields = '__all__'
        
class ReturnItemSerializer(serializers.ModelSerializer):
    product_obj = ProductSerializer(source='product', read_only=True)
    class Meta:
        model = ReturnItem
        fields = '__all__'
from rest_framework import serializers
from accounts.models import Stakeholder
from inventory.models import Order, OrderItem, Product, Return, ReturnItem, Payment
        
        
class StakeHolderSerializer(serializers.ModelSerializer):
    total_pending_amount = serializers.ReadOnlyField()
    next_bill_to_clear = serializers.ReadOnlyField()
    class Meta:
        model = Stakeholder
        fields = ('id', 'stakeholder_id', 'name', 'address', 'mobile', 'email', 'type', 'total_pending_amount', 'next_bill_to_clear')

class OrderSerializer(serializers.ModelSerializer):
    stakeholder_obj = StakeHolderSerializer(source='stakeholder', read_only=True)

    class Meta:
        model = Order
        fields = '__all__'
        
class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'

class OrderItemSerializer(serializers.ModelSerializer):
    product_obj = ProductSerializer(source='product', read_only=True)
    order_obj = OrderSerializer(source='order', read_only=True)
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
        
class PaymentSerializer(serializers.ModelSerializer):
    order_obj = OrderSerializer(source='order', read_only=True)
    company_obj = StakeHolderSerializer(source='company', read_only=True)
    class Meta:
        model = Payment
        fields = '__all__'
from rest_framework import serializers
from accounts.models import Stakeholder
from inventory.models import Order, OrderItem, Product, Return, ReturnItem, Payment, Invoice, InvoiceItem
        
        
class StakeHolderSerializer(serializers.ModelSerializer):
    total_pending_amount = serializers.ReadOnlyField()
    next_bill_to_clear = serializers.ReadOnlyField()
    total_setteled_amount = serializers.ReadOnlyField()
    class Meta:
        model = Stakeholder
        fields = ('id', 'stakeholder_id', 'name', 'address', 'mobile', 'email', 'type', 'total_pending_amount', 'next_bill_to_clear','total_setteled_amount', 'is_deleted', 'opening_balance')

class OrderSerializer(serializers.ModelSerializer):
    stakeholder_obj = StakeHolderSerializer(source='stakeholder', read_only=True)
    total_sales_orders = serializers.ReadOnlyField()
    total_purchase_orders = serializers.ReadOnlyField()

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
        
        
class InvoiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceItem
        fields = ['product', 'quantity', 'price', 'subtotal']


class InvoiceSerializer(serializers.ModelSerializer):
    items = InvoiceItemSerializer(many=True)

    class Meta:
        model = Invoice
        fields = [
            'id',
            'invoice_number',
            'invoice_type',
            'customer',
            'subtotal',
            'total_amount',
            'items'
        ]

    def create(self, validated_data):
        items_data = validated_data.pop('items')

        invoice = Invoice.objects.create(**validated_data)

        for item in items_data:
            InvoiceItem.objects.create(
                invoice=invoice,
                **item
            )

            # update stock
            product = item['product']
            # product.qty_available -= item['quantity']
            product.save()

        return invoice

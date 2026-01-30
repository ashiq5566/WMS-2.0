from rest_framework import serializers
from accounts.models import Stakeholder
import json
from inventory.models import Order, OrderItem, Product, Return, ReturnItem, Payment, Cart, CartItem, ProductSize
        
        
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

class ProductSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSize
        fields = ["id", "size", "price", "stock", "is_available"]
        
class ProductSerializer(serializers.ModelSerializer):
    sizes = ProductSizeSerializer(many=True, read_only=True)
    class Meta:
        model = Product
        fields = '__all__'

class ProductCreateSerializer(serializers.ModelSerializer):
    sizes = serializers.CharField(write_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "unit",
            "selling_price",
            "image",
            "sizes",
        ]

    def create(self, validated_data):
        # Extract sizes string
        sizes_data = validated_data.pop("sizes")

        # Convert JSON string → Python list
        sizes_data = json.loads(sizes_data)

        # Create product
        product = Product.objects.create(**validated_data)

        # Create sizes
        for size in sizes_data:
            ProductSize.objects.create(
                product=product,
                size=size["size"],
                price=size["price"],
                stock=size["stock"]
            )

        return product

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
        

class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    price = serializers.DecimalField(
        source="product.selling_price",
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    image = serializers.ImageField(
        source="product.image",
        read_only=True
    )
    size = serializers.CharField(source="size.size", read_only=True)


    class Meta:
        model = CartItem
        fields = ["id", "product", "product_name", "price", "quantity", 'image', 'size']


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = ["id", "items"]
        

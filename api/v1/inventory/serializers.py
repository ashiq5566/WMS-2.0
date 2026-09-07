from rest_framework import serializers
from accounts.models import Stakeholder
import json
from django.db import transaction
from inventory.models import Order, OrderItem, Product, Return, ReturnItem, Payment, Cart, CartItem, ProductSize, StockMovement
        
        
class StakeHolderSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=True, allow_blank=False)
    type = serializers.ChoiceField(choices=Stakeholder.STAKEHOLDER_TYPES, required=True)
    total_pending_amount = serializers.ReadOnlyField()
    next_bill_to_clear = serializers.ReadOnlyField()
    total_setteled_amount = serializers.ReadOnlyField()
    total_orders_count = serializers.ReadOnlyField()
    total_sales_amount = serializers.ReadOnlyField()
    total_returns_count = serializers.ReadOnlyField()

    class Meta:
        model = Stakeholder
        fields = (
            'id', 'stakeholder_id', 'name', 'company_name', 'contact_person',
            'address', 'shipping_address', 'city', 'state', 'country', 'postal_code',
            'mobile', 'alternate_phone', 'email', 'website', 'type',
            'tax_id', 'pan_number', 'payment_terms', 'credit_limit',
            'opening_balance', 'notes', 'is_active', 'is_deleted',
            'total_pending_amount', 'next_bill_to_clear', 'total_setteled_amount',
            'total_orders_count', 'total_sales_amount', 'total_returns_count',
            'date_added', 'date_updated'
        )
        read_only_fields = ('id', 'date_added', 'date_updated')

    def validate_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Stakeholder name is required.")
        return value.strip()

    def validate_type(self, value):
        if value not in ['Customer', 'Supplier']:
            raise serializers.ValidationError("Type must be either 'Customer' or 'Supplier'.")
        return value

    def validate(self, data):
        email = data.get('email')
        stakeholder_type = data.get('type') or (self.instance.type if self.instance else None)
        instance_id = self.instance.id if self.instance else None

        if email:
            qs = Stakeholder.objects.filter(email__iexact=email, type=stakeholder_type, is_deleted=False)
            if instance_id:
                qs = qs.exclude(id=instance_id)
            if qs.exists():
                raise serializers.ValidationError({"email": f"A {stakeholder_type} with this email already exists."})

        mobile = data.get('mobile')
        if mobile:
            qs = Stakeholder.objects.filter(mobile=mobile, type=stakeholder_type, is_deleted=False)
            if instance_id:
                qs = qs.exclude(id=instance_id)
            if qs.exists():
                raise serializers.ValidationError({"mobile": f"A {stakeholder_type} with this phone number already exists."})

        tax_id = data.get('tax_id')
        if tax_id:
            qs = Stakeholder.objects.filter(tax_id__iexact=tax_id, is_deleted=False)
            if instance_id:
                qs = qs.exclude(id=instance_id)
            if qs.exists():
                raise serializers.ValidationError({"tax_id": "A stakeholder with this Tax ID / GSTIN already exists."})

        return data


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
    qty_available = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = '__all__'
    
    def get_qty_available(self, obj):
        """Calculate available stock from all product sizes"""
        return sum(size.stock for size in obj.sizes.all())

class ProductCreateSerializer(serializers.ModelSerializer):
    sizes = serializers.CharField(write_only=True, required=False, allow_blank=True)
    qty_available = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "unit",
            "selling_price",
            "price_at_time_of_purchase",
            "qty_available",
            "image",
            "sizes",
            "status",
            "description",
        ]

    def get_qty_available(self, obj):
        """Calculate available stock from all product sizes"""
        return sum(size.stock for size in obj.sizes.all())

    def validate_sizes(self, value):
        if not value:
            return []
        try:
            sizes = json.loads(value)
        except (TypeError, json.JSONDecodeError):
            raise serializers.ValidationError('Sizes must be a JSON array.')

        if not isinstance(sizes, list):
            raise serializers.ValidationError('Sizes must be a JSON array.')

        validated_sizes = []
        for size in sizes:
            serializer = ProductSizeSerializer(data=size)
            serializer.is_valid(raise_exception=True)
            validated_sizes.append(serializer.validated_data)

        return validated_sizes

    def create(self, validated_data):
        sizes_data = validated_data.pop('sizes', [])

        with transaction.atomic():
            product = Product.objects.create(**validated_data)
            if sizes_data:
                ProductSize.objects.bulk_create([
                    ProductSize(
                        product=product,
                        size=size['size'],
                        price=size['price'],
                        stock=size['stock'],
                        is_available=size.get('is_available', True),
                    )
                    for size in sizes_data
                ])

        return product

    def update(self, instance, validated_data):
        sizes_data = validated_data.pop('sizes', None)

        with transaction.atomic():
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            if sizes_data is not None:
                instance.sizes.all().delete()
                ProductSize.objects.bulk_create([
                    ProductSize(
                        product=instance,
                        size=size['size'],
                        price=size['price'],
                        stock=size['stock'],
                        is_available=size.get('is_available', True),
                    )
                    for size in sizes_data
                ])

        return instance

class StockMovementSerializer(serializers.ModelSerializer):
    product_name = serializers.SerializerMethodField()
    
    class Meta:
        model = StockMovement
        fields = ['id', 'product_size', 'product_name', 'order', 'movement_type', 'quantity', 'reference', 'notes', 'created_at', 'created_by']
    
    def get_product_name(self, obj):
        return f"{obj.product_size.product.name} - Size {obj.product_size.size}"

class OrderItemSerializer(serializers.ModelSerializer):
    product_obj = ProductSerializer(source='product', read_only=True)
    order_obj = OrderSerializer(source='order', read_only=True)
    product_size_obj = ProductSizeSerializer(source='product_size', read_only=True)
    class Meta:
        model = OrderItem
        fields = '__all__'
        
class ReturnItemSerializer(serializers.ModelSerializer):
    product_obj = ProductSerializer(source='product', read_only=True)
    product_size_obj = ProductSizeSerializer(source='product_size', read_only=True)
    class Meta:
        model = ReturnItem
        fields = '__all__'
        
class ReturnSerializer(serializers.ModelSerializer):
    order_obj = OrderSerializer(source='original_order', read_only=True)
    items = ReturnItemSerializer(many=True, read_only=True)
    class Meta:
        model = Return
        fields = '__all__'
        
class PaymentSerializer(serializers.ModelSerializer):
    order_obj = OrderSerializer(source='order', read_only=True)
    company_obj = StakeHolderSerializer(source='company', read_only=True)

    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

    def validate_amount(self, value):
        if value is None or value <= 0:
            raise serializers.ValidationError("Payment amount must be greater than zero.")
        return value

    def validate(self, data):
        order = data.get('order')
        amount = data.get('amount')

        if order and amount:
            pending = order.pending_amount or 0
            if amount > pending:
                raise serializers.ValidationError({
                    "amount": f"Payment amount (₹{amount}) cannot exceed the outstanding balance (₹{pending}) of order #{order.id}."
                })
        return data


        

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
    size_price = serializers.CharField(source="size.price", read_only=True)


    class Meta:
        model = CartItem
        fields = ["id", "product", "product_name", "price", "quantity", 'image', 'size', 'size_price']


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = ["id", "items"]
        

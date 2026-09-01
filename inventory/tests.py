from django.test import TestCase
import json

from api.v1.inventory.serializers import ProductCreateSerializer
from inventory.models import Order, OrderItem, Product, ProductSize, Return, ReturnItem, StockMovement


class StockMovementTests(TestCase):
    def create_order(self, order_type, order_number):
        return Order.objects.create(
            order_type=order_type,
            order_number=order_number,
            gross_amount=0,
            discount=0,
            net_amount=0,
        )

    def test_sales_order_reduces_productsize_stock(self):
        """Test that SO (Sales Order) decreases ProductSize stock"""
        product = Product.objects.create(name='Sales stock product')
        product_size = ProductSize.objects.create(product=product, size=10, price=100, stock=10)
        order = self.create_order('SO', 'SO-STOCK-1')

        OrderItem.objects.create(
            order=order,
            product=product,
            product_size=product_size,
            quantity=3,
            price_at_time_of_order=100,
        )

        product_size.refresh_from_db()
        # Stock should decrease by 3
        self.assertEqual(product_size.stock, 7)
        # Verify qty_available (computed property)
        self.assertEqual(product.qty_available, 7)

    def test_purchase_order_increases_productsize_stock(self):
        """Test that PO (Purchase Order) increases ProductSize stock"""
        product = Product.objects.create(name='Purchase stock product')
        product_size = ProductSize.objects.create(product=product, size=10, price=100, stock=10)
        order = self.create_order('PO', 'PO-STOCK-1')

        OrderItem.objects.create(
            order=order,
            product=product,
            product_size=product_size,
            quantity=5,
            price_at_time_of_order=100,
        )

        product_size.refresh_from_db()
        # Stock should increase by 5
        self.assertEqual(product_size.stock, 15)
        # Verify qty_available (computed property)
        self.assertEqual(product.qty_available, 15)

    def test_stock_movement_created_on_order_item_save(self):
        """Test that StockMovement record is created for audit trail"""
        product = Product.objects.create(name='Audit test product')
        product_size = ProductSize.objects.create(product=product, size=10, price=100, stock=10)
        order = self.create_order('SO', 'SO-AUDIT-1')

        OrderItem.objects.create(
            order=order,
            product=product,
            product_size=product_size,
            quantity=3,
            price_at_time_of_order=100,
        )

        # Verify StockMovement was created
        movements = StockMovement.objects.filter(product_size=product_size)
        self.assertEqual(movements.count(), 1)
        
        movement = movements.first()
        self.assertEqual(movement.movement_type, 'SALE')
        self.assertEqual(movement.quantity, -3)  # Negative for outbound
        self.assertEqual(movement.reference, 'SO-AUDIT-1')


class ProductCreationTests(TestCase):
    def test_sized_product_calculates_qty_available_from_sizes(self):
        """Test that qty_available is calculated from all ProductSize stocks"""
        serializer = ProductCreateSerializer(data={
            'name': 'Sized stock product',
            'unit': 'Pieces',
            'selling_price': 250,
            'sizes': json.dumps([
                {'size': 8, 'price': 250, 'stock': 3},
                {'size': 9, 'price': 260, 'stock': 5},
            ]),
        })

        self.assertTrue(serializer.is_valid(), serializer.errors)
        product = serializer.save()
        product.refresh_from_db()

        # qty_available should be sum of all sizes: 3 + 5 = 8
        self.assertEqual(product.qty_available, 8)
        self.assertEqual(product.product_id, f'PR{product.pk}')
        self.assertEqual(product.sizes.count(), 2)

    def test_product_without_sizes_has_zero_qty_available(self):
        """Test that product without sizes has qty_available of 0"""
        serializer = ProductCreateSerializer(data={
            'name': 'Product without sizes',
            'unit': 'Pieces',
            'selling_price': 100,
            'sizes': '[]',
        })

        self.assertTrue(serializer.is_valid(), serializer.errors)
        product = serializer.save()

        # qty_available should be 0 since no sizes
        self.assertEqual(product.qty_available, 0)

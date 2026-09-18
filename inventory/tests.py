from django.test import TestCase
import json
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from api.v1.inventory.serializers import ProductCreateSerializer
from inventory.models import Order, OrderItem, Product, ProductSize, Return, ReturnItem, StockMovement, Payment




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

    def test_product_update_without_sizes(self):
        """Test updating product details without providing sizes (row editing)"""
        product = Product.objects.create(name='Update Test', selling_price=100, price_at_time_of_purchase=50)
        serializer = ProductCreateSerializer(instance=product, data={
            'name': 'Update Test Renamed',
            'selling_price': 120,
            'price_at_time_of_purchase': 60
        }, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()
        self.assertEqual(updated.name, 'Update Test Renamed')
        self.assertEqual(updated.selling_price, 120)
        self.assertEqual(updated.price_at_time_of_purchase, 60)


from rest_framework.test import APIClient
from accounts.models import User, Stakeholder


class OrderFlowAndCancellationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='orderuser', password='password123')
        self.client.force_authenticate(user=self.user)
        self.customer = Stakeholder.objects.create(name='Test Customer', type='Customer')
        self.supplier = Stakeholder.objects.create(name='Test Supplier', type='Supplier')
        self.product = Product.objects.create(name='Widget Product', selling_price=150)
        self.size1 = ProductSize.objects.create(product=self.product, size=1, price=100, stock=20)

    def test_create_sales_order_deducts_stock(self):
        payload = {
            'order': {
                'order_type': 'SO',
                'stakeholder': self.customer.id,
                'gross_amount': 300,
                'discount': 0,
                'net_amount': 300
            },
            'items': [
                {
                    'product': self.product.id,
                    'product_size': self.size1.id,
                    'quantity': 5,
                    'price_at_time_of_order': 60,
                    'total': 300
                }
            ]
        }
        res = self.client.post('/api/inventory/orders/', payload, format='json')
        self.assertEqual(res.status_code, 201)
        self.size1.refresh_from_db()
        self.assertEqual(self.size1.stock, 15)

    def test_create_sales_order_insufficient_stock_fails(self):
        payload = {
            'order': {
                'order_type': 'SO',
                'stakeholder': self.customer.id,
                'gross_amount': 3000,
                'discount': 0,
                'net_amount': 3000
            },
            'items': [
                {
                    'product': self.product.id,
                    'product_size': self.size1.id,
                    'quantity': 50,  # exceeds available 20
                    'price_at_time_of_order': 60,
                    'total': 3000
                }
            ]
        }
        res = self.client.post('/api/inventory/orders/', payload, format='json')
        self.assertEqual(res.status_code, 400)
        self.assertIn('Insufficient stock', str(res.data))
        self.size1.refresh_from_db()
        self.assertEqual(self.size1.stock, 20)  # Stock untouched

    def test_cancel_sales_order_restores_stock(self):
        # Create SO
        payload = {
            'order': {
                'order_type': 'SO',
                'stakeholder': self.customer.id,
                'gross_amount': 200,
                'discount': 0,
                'net_amount': 200
            },
            'items': [
                {
                    'product': self.product.id,
                    'product_size': self.size1.id,
                    'quantity': 8,
                    'price_at_time_of_order': 25,
                    'total': 200
                }
            ]
        }
        res = self.client.post('/api/inventory/orders/', payload, format='json')
        self.assertEqual(res.status_code, 201)
        order_id = res.data['order']['id']
        self.size1.refresh_from_db()
        self.assertEqual(self.size1.stock, 12)

        # Cancel SO
        cancel_res = self.client.post(f'/api/inventory/orders/{order_id}/cancel/')
        self.assertEqual(cancel_res.status_code, 200)
        self.size1.refresh_from_db()
        # Stock restored from 12 back to 20
        self.assertEqual(self.size1.stock, 20)
        order = Order.objects.get(id=order_id)
        self.assertEqual(order.order_status, 'Cancelled')

    def test_cancel_purchase_order_deducts_stock(self):
        # Create PO
        payload = {
            'order': {
                'order_type': 'PO',
                'stakeholder': self.supplier.id,
                'gross_amount': 500,
                'discount': 0,
                'net_amount': 500
            },
            'items': [
                {
                    'product': self.product.id,
                    'product_size': self.size1.id,
                    'quantity': 10,
                    'price_at_time_of_order': 50,
                    'total': 500
                }
            ]
        }
        res = self.client.post('/api/inventory/orders/', payload, format='json')
        self.assertEqual(res.status_code, 201)
        order_id = res.data['order']['id']
        self.size1.refresh_from_db()
        self.assertEqual(self.size1.stock, 30)  # 20 + 10 = 30

        # Cancel PO
        cancel_res = self.client.post(f'/api/inventory/orders/{order_id}/cancel/')
        self.assertEqual(cancel_res.status_code, 200)
        self.size1.refresh_from_db()
        # Stock deducted from 30 back to 20
        self.assertEqual(self.size1.stock, 20)
        order = Order.objects.get(id=order_id)
        self.assertEqual(order.order_status, 'Cancelled')


class ReturnFlowAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='returnuser', password='password123')
        self.client.force_authenticate(user=self.user)
        self.customer = Stakeholder.objects.create(name='Return Customer', type='Customer')
        self.supplier = Stakeholder.objects.create(name='Return Supplier', type='Supplier')
        self.product = Product.objects.create(name='Returnable Product', selling_price=100)
        self.size = ProductSize.objects.create(product=self.product, size=1, price=100, stock=20)

    def test_sales_return_increases_stock_and_creates_stock_movement(self):
        # 1. Create SO for 10 units
        so_payload = {
            'order': {
                'order_type': 'SO',
                'stakeholder': self.customer.id,
                'gross_amount': 1000,
                'discount': 0,
                'net_amount': 1000
            },
            'items': [
                {
                    'product': self.product.id,
                    'product_size': self.size.id,
                    'quantity': 10,
                    'price_at_time_of_order': 100,
                    'total': 1000
                }
            ]
        }
        res = self.client.post('/api/inventory/orders/', so_payload, format='json')
        self.assertEqual(res.status_code, 201)
        order_id = res.data['order']['id']
        self.size.refresh_from_db()
        self.assertEqual(self.size.stock, 10)  # 20 - 10 = 10

        # 2. Return 4 units
        ret_payload = {
            'return': {
                'original_order': order_id,
                'return_type': 'SR',
                'total_amount': 400
            },
            'items': [
                {
                    'product': self.product.id,
                    'product_size': self.size.id,
                    'quantity': 4,
                    'price_at_return': 100,
                    'total': 400
                }
            ]
        }
        ret_res = self.client.post('/api/inventory/returns/', ret_payload, format='json')
        self.assertEqual(ret_res.status_code, 201)

        # 3. Stock increases from 10 back to 14
        self.size.refresh_from_db()
        self.assertEqual(self.size.stock, 14)

        # 4. Order financial balance updated safely
        order = Order.objects.get(id=order_id)
        self.assertEqual(order.total_amount, 600)
        self.assertEqual(order.pending_amount, 600)

        # 5. Stock movement created
        movement = StockMovement.objects.filter(product_size=self.size, movement_type='RETURN_SALE').latest('id')
        self.assertEqual(movement.quantity, 4)

    def test_purchase_return_decreases_stock_and_creates_stock_movement(self):
        # 1. Create PO for 10 units
        po_payload = {
            'order': {
                'order_type': 'PO',
                'stakeholder': self.supplier.id,
                'gross_amount': 1000,
                'discount': 0,
                'net_amount': 1000
            },
            'items': [
                {
                    'product': self.product.id,
                    'product_size': self.size.id,
                    'quantity': 10,
                    'price_at_time_of_order': 100,
                    'total': 1000
                }
            ]
        }
        res = self.client.post('/api/inventory/orders/', po_payload, format='json')
        self.assertEqual(res.status_code, 201)
        order_id = res.data['order']['id']
        self.size.refresh_from_db()
        self.assertEqual(self.size.stock, 30)  # 20 + 10 = 30

        # 2. Return 5 units to supplier
        ret_payload = {
            'return': {
                'original_order': order_id,
                'return_type': 'PR',
                'total_amount': 500
            },
            'items': [
                {
                    'product': self.product.id,
                    'product_size': self.size.id,
                    'quantity': 5,
                    'price_at_return': 100,
                    'total': 500
                }
            ]
        }
        ret_res = self.client.post('/api/inventory/returns/', ret_payload, format='json')
        self.assertEqual(ret_res.status_code, 201)

        # 3. Stock decreases from 30 to 25
        self.size.refresh_from_db()
        self.assertEqual(self.size.stock, 25)

        # 4. Stock movement created
        movement = StockMovement.objects.filter(product_size=self.size, movement_type='RETURN_PURCHASE').latest('id')
        self.assertEqual(movement.quantity, -5)

    def test_return_over_order_quantity_rejected(self):
        po_payload = {
            'order': {
                'order_type': 'PO',
                'stakeholder': self.supplier.id,
                'gross_amount': 500,
                'discount': 0,
                'net_amount': 500
            },
            'items': [
                {
                    'product': self.product.id,
                    'product_size': self.size.id,
                    'quantity': 5,
                    'price_at_time_of_order': 100,
                    'total': 500
                }
            ]
        }
        res = self.client.post('/api/inventory/orders/', po_payload, format='json')
        order_id = res.data['order']['id']

        # Attempt to return 6 units when order had only 5
        ret_payload = {
            'return': {
                'original_order': order_id,
                'return_type': 'PR',
                'total_amount': 600
            },
            'items': [
                {
                    'product': self.product.id,
                    'product_size': self.size.id,
                    'quantity': 6,
                    'price_at_return': 100,
                    'total': 600
                }
            ]
        }
        ret_res = self.client.post('/api/inventory/returns/', ret_payload, format='json')
        self.assertEqual(ret_res.status_code, 400)
        self.assertIn('Max returnable', ret_res.data['error'])

    def test_cumulative_returns_exceeding_order_quantity_rejected(self):
        po_payload = {
            'order': {
                'order_type': 'PO',
                'stakeholder': self.supplier.id,
                'gross_amount': 500,
                'discount': 0,
                'net_amount': 500
            },
            'items': [
                {
                    'product': self.product.id,
                    'product_size': self.size.id,
                    'quantity': 5,
                    'price_at_time_of_order': 100,
                    'total': 500
                }
            ]
        }
        res = self.client.post('/api/inventory/orders/', po_payload, format='json')
        order_id = res.data['order']['id']

        # First return of 3 units succeeds
        ret_payload_1 = {
            'return': {
                'original_order': order_id,
                'return_type': 'PR',
                'total_amount': 300
            },
            'items': [
                {
                    'product': self.product.id,
                    'product_size': self.size.id,
                    'quantity': 3,
                    'price_at_return': 100,
                    'total': 300
                }
            ]
        }
        ret_res_1 = self.client.post('/api/inventory/returns/', ret_payload_1, format='json')
        self.assertEqual(ret_res_1.status_code, 201)

        # Second return of 3 units should fail (3 + 3 = 6 > 5)
        ret_payload_2 = {
            'return': {
                'original_order': order_id,
                'return_type': 'PR',
                'total_amount': 300
            },
            'items': [
                {
                    'product': self.product.id,
                    'product_size': self.size.id,
                    'quantity': 3,
                    'price_at_return': 100,
                    'total': 300
                }
            ]
        }
        ret_res_2 = self.client.post('/api/inventory/returns/', ret_payload_2, format='json')
        self.assertEqual(ret_res_2.status_code, 400)
        self.assertIn('Max returnable', ret_res_2.data['error'])

    def test_purchase_return_insufficient_stock_rejected(self):
        # Set stock to 2
        self.size.stock = 2
        self.size.save()

        # Create PO for 5 units (stock becomes 7)
        po_payload = {
            'order': {
                'order_type': 'PO',
                'stakeholder': self.supplier.id,
                'gross_amount': 500,
                'discount': 0,
                'net_amount': 500
            },
            'items': [
                {
                    'product': self.product.id,
                    'product_size': self.size.id,
                    'quantity': 5,
                    'price_at_time_of_order': 100,
                    'total': 500
                }
            ]
        }
        res = self.client.post('/api/inventory/orders/', po_payload, format='json')
        order_id = res.data['order']['id']

        # Now simulate warehouse stock being drained down to 1 by sales or adjustments
        self.size.stock = 1
        self.size.save()

        # Try to return 3 units to supplier
        ret_payload = {
            'return': {
                'original_order': order_id,
                'return_type': 'PR',
                'total_amount': 300
            },
            'items': [
                {
                    'product': self.product.id,
                    'product_size': self.size.id,
                    'quantity': 3,
                    'price_at_return': 100,
                    'total': 300
                }
            ]
        }
        ret_res = self.client.post('/api/inventory/returns/', ret_payload, format='json')
        self.assertEqual(ret_res.status_code, 400)
        self.assertIn('Insufficient warehouse stock', ret_res.data['error'])

    def test_return_on_cancelled_order_rejected(self):
        po_payload = {
            'order': {
                'order_type': 'PO',
                'stakeholder': self.supplier.id,
                'gross_amount': 500,
                'discount': 0,
                'net_amount': 500
            },
            'items': [
                {
                    'product': self.product.id,
                    'product_size': self.size.id,
                    'quantity': 5,
                    'price_at_time_of_order': 100,
                    'total': 500
                }
            ]
        }
        res = self.client.post('/api/inventory/orders/', po_payload, format='json')
        order_id = res.data['order']['id']

        # Cancel the order
        self.client.post(f'/api/inventory/orders/{order_id}/cancel/')

        # Attempt to return
        ret_payload = {
            'return': {
                'original_order': order_id,
                'return_type': 'PR',
                'total_amount': 200
            },
            'items': [
                {
                    'product': self.product.id,
                    'product_size': self.size.id,
                    'quantity': 2,
                    'price_at_return': 100,
                    'total': 200
                }
            ]
        }
        ret_res = self.client.post('/api/inventory/returns/', ret_payload, format='json')
        self.assertEqual(ret_res.status_code, 400)
        self.assertIn('Cannot process return for a cancelled order', ret_res.data['error'])

    def test_draft_return_does_not_alter_stock_until_approved(self):
        so_payload = {
            'order': {
                'order_type': 'SO',
                'stakeholder': self.customer.id,
                'gross_amount': 1000,
                'discount': 0,
                'net_amount': 1000
            },
            'items': [
                {
                    'product': self.product.id,
                    'product_size': self.size.id,
                    'quantity': 10,
                    'price_at_time_of_order': 100,
                    'total': 1000
                }
            ]
        }
        res = self.client.post('/api/inventory/orders/', so_payload, format='json')
        order_id = res.data['order']['id']
        self.size.refresh_from_db()
        self.assertEqual(self.size.stock, 10)  # 20 - 10 = 10

        # Submit Draft return
        draft_payload = {
            'return': {
                'original_order': order_id,
                'return_type': 'SR',
                'return_status': 'Draft',
                'total_amount': 300
            },
            'items': [
                {
                    'product': self.product.id,
                    'product_size': self.size.id,
                    'quantity': 3,
                    'price_at_return': 100,
                    'total': 300
                }
            ]
        }
        draft_res = self.client.post('/api/inventory/returns/', draft_payload, format='json')
        self.assertEqual(draft_res.status_code, 201)
        return_id = draft_res.data['return']['id']

        # Verify stock and order balances were NOT altered during Draft stage
        self.size.refresh_from_db()
        self.assertEqual(self.size.stock, 10)
        order = Order.objects.get(id=order_id)
        self.assertEqual(order.total_amount, 1000)

        # Now approve return
        app_res = self.client.post(f'/api/inventory/returns/{return_id}/approve/')
        self.assertEqual(app_res.status_code, 200)

        # After approval: stock is restored and order balance adjusted
        self.size.refresh_from_db()
        self.assertEqual(self.size.stock, 13)
        order.refresh_from_db()
        self.assertEqual(order.total_amount, 700)
        self.assertEqual(order.pending_amount, 700)

    def test_damaged_sales_return_quarantine_handling(self):
        so_payload = {
            'order': {
                'order_type': 'SO',
                'stakeholder': self.customer.id,
                'gross_amount': 500,
                'discount': 0,
                'net_amount': 500
            },
            'items': [
                {
                    'product': self.product.id,
                    'product_size': self.size.id,
                    'quantity': 5,
                    'price_at_time_of_order': 100,
                    'total': 500
                }
            ]
        }
        res = self.client.post('/api/inventory/orders/', so_payload, format='json')
        order_id = res.data['order']['id']
        self.size.refresh_from_db()
        self.assertEqual(self.size.stock, 15)  # 20 - 5 = 15

        # Return 2 units with condition 'Damaged'
        ret_payload = {
            'return': {
                'original_order': order_id,
                'return_type': 'SR',
                'total_amount': 200
            },
            'items': [
                {
                    'product': self.product.id,
                    'product_size': self.size.id,
                    'quantity': 2,
                    'price_at_return': 100,
                    'total': 200,
                    'condition': 'Damaged',
                    'reason': 'Damaged in transit'
                }
            ]
        }
        ret_res = self.client.post('/api/inventory/returns/', ret_payload, format='json')
        self.assertEqual(ret_res.status_code, 201)

        # Sellable stock must NOT increase for damaged goods
        self.size.refresh_from_db()
        self.assertEqual(self.size.stock, 15)

        # But financial credit is still provided to customer
        order = Order.objects.get(id=order_id)
        self.assertEqual(order.total_amount, 300)

    def test_duplicate_item_lines_in_return_payload_rejected(self):
        po_payload = {
            'order': {
                'order_type': 'PO',
                'stakeholder': self.supplier.id,
                'gross_amount': 500,
                'discount': 0,
                'net_amount': 500
            },
            'items': [
                {
                    'product': self.product.id,
                    'product_size': self.size.id,
                    'quantity': 5,
                    'price_at_time_of_order': 100,
                    'total': 500
                }
            ]
        }
        res = self.client.post('/api/inventory/orders/', po_payload, format='json')
        order_id = res.data['order']['id']

        # Duplicate product_size in items
        ret_payload = {
            'return': {
                'original_order': order_id,
                'return_type': 'PR',
                'total_amount': 200
            },
            'items': [
                {
                    'product': self.product.id,
                    'product_size': self.size.id,
                    'quantity': 1,
                    'price_at_return': 100,
                    'total': 100
                },
                {
                    'product': self.product.id,
                    'product_size': self.size.id,
                    'quantity': 1,
                    'price_at_return': 100,
                    'total': 100
                }
            ]
        }
        ret_res = self.client.post('/api/inventory/returns/', ret_payload, format='json')
        self.assertEqual(ret_res.status_code, 400)
        self.assertIn('Duplicate product variant', ret_res.data['error'])


class PaymentAndFinancialTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='fin_admin', password='password123', user_type='admin')
        self.client.force_authenticate(user=self.user)
        self.customer = Stakeholder.objects.create(name='Fin Customer', type='Customer')
        self.supplier = Stakeholder.objects.create(name='Fin Supplier', type='Supplier')

        self.so_order = Order.objects.create(
            order_number='SO-FIN-001',
            stakeholder=self.customer,
            order_type='SO',
            order_status='Issued',
            net_amount=1000,
            total_amount=1000,
            pending_amount=1000,
            date_added=timezone.now()
        )

        self.po_order = Order.objects.create(
            order_number='PO-FIN-001',
            stakeholder=self.supplier,
            order_type='PO',
            order_status='Issued',
            net_amount=2500,
            total_amount=2500,
            pending_amount=2500,
            date_added=timezone.now()
        )


    def test_inbound_payment_auto_number_and_deduction(self):
        """Inbound customer payment auto-generates REC-XXXXX and decrements pending_amount"""
        payload = {
            'order': self.so_order.id,
            'amount': 400,
            'payment_date': timezone.now().isoformat(),
            'payment_method': 'CASH',
            'reference': 'CASH-REC-01'
        }
        res = self.client.post('/api/inventory/payments/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(res.data['payment_number'].startswith('REC-'))
        self.assertEqual(res.data['payment_type'], 'INBOUND')

        self.so_order.refresh_from_db()
        self.assertEqual(self.so_order.pending_amount, 600)
        self.assertEqual(self.so_order.order_status, 'Issued')

    def test_payment_full_liquidation_closes_order(self):
        """Fully paying off pending balance automatically transitions order to Closed"""
        payload = {
            'order': self.so_order.id,
            'amount': 1000,
            'payment_date': timezone.now().isoformat(),
            'payment_method': 'BANK',
            'reference': 'NEFT-123456'
        }
        res = self.client.post('/api/inventory/payments/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        self.so_order.refresh_from_db()
        self.assertEqual(self.so_order.pending_amount, 0)
        self.assertEqual(self.so_order.order_status, 'Closed')

    def test_overpayment_rejected(self):
        """Submitting payment exceeding order pending balance is rejected"""
        payload = {
            'order': self.so_order.id,
            'amount': 1500,  # exceeds 1000
            'payment_date': timezone.now().isoformat(),
            'payment_method': 'CARD'
        }
        res = self.client.post('/api/inventory/payments/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('amount', res.data)

        self.so_order.refresh_from_db()
        self.assertEqual(self.so_order.pending_amount, 1000)

    def test_outbound_supplier_payment(self):
        """PO payments are classified as OUTBOUND and numbered PAY-XXXXX"""
        payload = {
            'order': self.po_order.id,
            'amount': 2500,
            'payment_date': timezone.now().isoformat(),
            'payment_method': 'BANK',
            'reference': 'RTGS-9988'
        }
        res = self.client.post('/api/inventory/payments/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(res.data['payment_number'].startswith('PAY-'))
        self.assertEqual(res.data['payment_type'], 'OUTBOUND')

        self.po_order.refresh_from_db()
        self.assertEqual(self.po_order.pending_amount, 0)
        self.assertEqual(self.po_order.order_status, 'Closed')

    def test_financial_summary_analytics_endpoint(self):
        """Financial summary endpoint returns complete executive metrics"""
        # Create an inbound payment
        Payment.objects.create(
            order=self.so_order,
            amount=500,
            payment_date=timezone.now(),
            payment_method='CASH',
            payment_type='INBOUND',
            status='Completed'
        )
        # Create an outbound payment
        Payment.objects.create(
            order=self.po_order,
            amount=1000,
            payment_date=timezone.now(),
            payment_method='BANK',
            payment_type='OUTBOUND',
            status='Completed'
        )

        res = self.client.get('/api/inventory/payments/financial_summary/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('total_revenue', res.data)
        self.assertIn('total_received', res.data)
        self.assertIn('total_paid', res.data)
        self.assertIn('net_cash_flow', res.data)
        self.assertIn('outstanding_receivables', res.data)
        self.assertIn('outstanding_payables', res.data)
        self.assertIn('monthly_trends', res.data)
        self.assertIn('sales_settlement_pct', res.data)
        self.assertIn('purchase_settlement_pct', res.data)
        self.assertIn('settlement_breakdown', res.data)
        self.assertEqual(res.data['total_received'], 500)
        self.assertEqual(res.data['total_paid'], 1000)
        self.assertEqual(res.data['net_cash_flow'], -500)

    def test_fifo_unallocated_payment_with_opening_balance(self):
        """Unallocated payment first drains opening_balance then applies remainder to oldest order"""
        stakeholder = Stakeholder.objects.create(name='FIFO OB Customer', type='Customer', opening_balance=500)
        oldest_order = Order.objects.create(
            order_number='SO-FIFO-001',
            stakeholder=stakeholder,
            order_type='SO',
            order_status='Issued',
            net_amount=1000,
            total_amount=1000,
            pending_amount=1000,
            date_added=timezone.now()
        )

        # Payment of 700: 500 covers opening_balance, 200 decrements oldest order
        payment = Payment.objects.create(
            company=stakeholder,
            order=None,
            amount=700,
            payment_date=timezone.now(),
            payment_method='CASH',
            status='Completed'
        )

        stakeholder.refresh_from_db()
        self.assertEqual(stakeholder.opening_balance, 0)
        oldest_order.refresh_from_db()
        self.assertEqual(oldest_order.pending_amount, 800)
        self.assertEqual(oldest_order.order_status, 'Issued')
        self.assertEqual(payment.order, oldest_order)

    def test_fifo_unallocated_payment_without_opening_balance_closes_order(self):
        """Unallocated payment with zero opening balance applies to oldest order and closes it when fully paid"""
        stakeholder = Stakeholder.objects.create(name='FIFO Zero OB Customer', type='Customer', opening_balance=0)
        import datetime
        now = timezone.now()
        order_old = Order.objects.create(
            order_number='SO-FIFO-OLD',
            stakeholder=stakeholder,
            order_type='SO',
            order_status='Issued',
            net_amount=600,
            total_amount=600,
            pending_amount=600,
            date_added=now - datetime.timedelta(days=2)
        )
        order_new = Order.objects.create(
            order_number='SO-FIFO-NEW',
            stakeholder=stakeholder,
            order_type='SO',
            order_status='Issued',
            net_amount=400,
            total_amount=400,
            pending_amount=400,
            date_added=now
        )

        # Pay 600 unallocated
        payment = Payment.objects.create(
            company=stakeholder,
            order=None,
            amount=600,
            payment_date=now,
            payment_method='BANK',
            status='Completed'
        )

        order_old.refresh_from_db()
        order_new.refresh_from_db()
        self.assertEqual(order_old.pending_amount, 0)
        self.assertEqual(order_old.order_status, 'Closed')
        self.assertEqual(order_new.pending_amount, 400)
        self.assertEqual(order_new.order_status, 'Issued')
        self.assertEqual(payment.order, order_old)

    def test_return_financial_reconciliation_clamping(self):
        """Return deduction safely clamps order total_amount and pending_amount to 0 to prevent underflow"""
        order = Order.objects.create(
            order_number='SO-CLAMP-001',
            stakeholder=self.customer,
            order_type='SO',
            order_status='Issued',
            net_amount=500,
            date_added=timezone.now()
        )
        # Simulate partial payment having been made earlier
        Order.objects.filter(id=order.id).update(pending_amount=300)

        # Process return with total_amount 400 (exceeds pending 300)
        ret = Return.objects.create(
            original_order=order,
            return_type='SR',
            return_status='Completed',
            total_amount=400,
            stock_adjusted=False
        )

        order.refresh_from_db()
        self.assertEqual(order.total_amount, 100)  # max(0, 500 - 400) = 100
        self.assertEqual(order.pending_amount, 0)   # max(0, 300 - 400) clamped to 0

    def test_insufficient_stock_aborts_transaction_and_rolls_back(self):
        """When multi-line SO has insufficient stock on later item, entire transaction rolls back cleanly"""
        product = Product.objects.create(name='Atomic Rollback Product', selling_price=100)
        size_ok = ProductSize.objects.create(product=product, size=1, price=100, stock=10)
        size_short = ProductSize.objects.create(product=product, size=2, price=100, stock=2)

        initial_order_count = Order.objects.count()
        initial_orderitem_count = OrderItem.objects.count()

        payload = {
            'order': {
                'order_type': 'SO',
                'stakeholder': self.customer.id,
                'gross_amount': 500,
                'discount': 0,
                'net_amount': 500
            },
            'items': [
                {
                    'product': product.id,
                    'product_size': size_ok.id,
                    'quantity': 3,
                    'price_at_time_of_order': 100,
                    'total': 300
                },
                {
                    'product': product.id,
                    'product_size': size_short.id,
                    'quantity': 10,  # Exceeds available 2!
                    'price_at_time_of_order': 100,
                    'total': 200
                }
            ]
        }

        res = self.client.post('/api/inventory/orders/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Insufficient stock', res.data['error'])

        # Verify full transaction rollback: no new orders, no orphaned items, stock untouched
        self.assertEqual(Order.objects.count(), initial_order_count)
        self.assertEqual(OrderItem.objects.count(), initial_orderitem_count)
        size_ok.refresh_from_db()
        size_short.refresh_from_db()
        self.assertEqual(size_ok.stock, 10)
        self.assertEqual(size_short.stock, 2)


class ProfitAnalyticsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='profit_analyst', password='password123', user_type='admin')
        self.client.force_authenticate(user=self.user)
        self.customer1 = Stakeholder.objects.create(name='Acme Retail', type='Customer')
        self.customer2 = Stakeholder.objects.create(name='Beta Stores', type='Customer')

        # Product with base purchase cost of 60, selling price of 100
        self.product = Product.objects.create(
            name='Analytics Shoe',
            selling_price=100,
            price_at_time_of_purchase=60,
            unit='Pieces'
        )
        # Size 8: fallback to base product cost (price_at_time_of_purchase=None)
        self.size8 = ProductSize.objects.create(
            product=self.product,
            size=8,
            price=100,
            stock=50,
            price_at_time_of_purchase=None
        )
        # Size 9: explicit size-level cost of 70 (higher than base 60)
        self.size9 = ProductSize.objects.create(
            product=self.product,
            size=9,
            price=120,
            stock=50,
            price_at_time_of_purchase=70
        )

    def test_profit_analytics_base_product_cost_fallback(self):
        """When size price_at_time_of_purchase is null, COGS falls back to Product.price_at_time_of_purchase"""
        order = Order.objects.create(
            order_number='SO-PROFIT-01',
            stakeholder=self.customer1,
            order_type='SO',
            order_status='Delivered',
            gross_amount=1000,
            discount=0,
            net_amount=1000,
            order_date=timezone.now()
        )
        # 10 units of size 8 at 100/unit = 1000 revenue. Unit cost = 60 (fallback). COGS = 600. Gross Profit = 400. Margin = 40.0%
        OrderItem.objects.create(
            order=order,
            product=self.product,
            product_size=self.size8,
            quantity=10,
            price_at_time_of_order=100,
            total=1000
        )

        res = self.client.get('/api/inventory/profit-analytics/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        kpi = res.data['kpi']
        self.assertEqual(kpi['total_revenue'], 1000.0)
        self.assertEqual(kpi['total_cogs'], 600.0)
        self.assertEqual(kpi['gross_profit'], 400.0)
        self.assertEqual(kpi['profit_margin_pct'], 40.0)

    def test_profit_analytics_size_specific_cost(self):
        """When size has price_at_time_of_purchase, it overrides base product cost"""
        order = Order.objects.create(
            order_number='SO-PROFIT-02',
            stakeholder=self.customer1,
            order_type='SO',
            order_status='Closed',
            gross_amount=1200,
            discount=0,
            net_amount=1200,
            order_date=timezone.now()
        )
        # 10 units of size 9 at 120/unit = 1200 revenue. Unit cost = 70. COGS = 700. Gross Profit = 500. Margin = 41.7%
        OrderItem.objects.create(
            order=order,
            product=self.product,
            product_size=self.size9,
            quantity=10,
            price_at_time_of_order=120,
            total=1200
        )

        res = self.client.get('/api/inventory/profit-analytics/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        kpi = res.data['kpi']
        self.assertEqual(kpi['total_revenue'], 1200.0)
        self.assertEqual(kpi['total_cogs'], 700.0)
        self.assertEqual(kpi['gross_profit'], 500.0)
        self.assertEqual(kpi['profit_margin_pct'], 41.7)

    def test_profit_analytics_sales_returns_deduction(self):
        """Sales Returns deduct refunded quantities, refunded revenue, and COGS from net profit"""
        order = Order.objects.create(
            order_number='SO-PROFIT-03',
            stakeholder=self.customer1,
            order_type='SO',
            order_status='Issued',
            gross_amount=1000,
            discount=0,
            net_amount=1000,
            order_date=timezone.now()
        )
        # Sold 10 units of size 8: Revenue = 1000, COGS = 600
        OrderItem.objects.create(
            order=order,
            product=self.product,
            product_size=self.size8,
            quantity=10,
            price_at_time_of_order=100,
            total=1000
        )

        # Process return for 2 units: Refunded Rev = 200, Returned COGS = 120
        ret = Return.objects.create(
            original_order=order,
            return_type='SR',
            return_status='Completed',
            total_amount=200,
            stock_adjusted=True
        )
        ReturnItem.objects.create(
            return_order=ret,
            product=self.product,
            product_size=self.size8,
            quantity=2,
            price_at_return=100,
            total=200,
            condition='Good'
        )

        res = self.client.get('/api/inventory/profit-analytics/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        kpi = res.data['kpi']
        # Net Revenue = 1000 - 200 = 800
        # Net COGS = 600 - 120 = 480
        # Net Gross Profit = 800 - 480 = 320
        # Net Margin = (320 / 800) * 100 = 40.0%
        self.assertEqual(kpi['total_revenue'], 800.0)
        self.assertEqual(kpi['total_cogs'], 480.0)
        self.assertEqual(kpi['gross_profit'], 320.0)
        self.assertEqual(kpi['profit_margin_pct'], 40.0)
        self.assertEqual(kpi['total_returned_units'], 2)
        self.assertEqual(kpi['total_returned_revenue'], 200.0)

    def test_profit_analytics_negative_profit_discount(self):
        """When sold below purchase cost, negative gross profit and negative margin are safely handled"""
        order = Order.objects.create(
            order_number='SO-LOSS-01',
            stakeholder=self.customer1,
            order_type='SO',
            order_status='Closed',
            gross_amount=400,
            discount=0,
            net_amount=400,
            order_date=timezone.now()
        )
        # Sold 10 units at 40/unit (clearance), while purchase cost was 60/unit
        # Revenue = 400, COGS = 600, Gross Profit = -200, Margin = (-200 / 400) * 100 = -50.0%
        OrderItem.objects.create(
            order=order,
            product=self.product,
            product_size=self.size8,
            quantity=10,
            price_at_time_of_order=40,
            total=400
        )

        res = self.client.get('/api/inventory/profit-analytics/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        kpi = res.data['kpi']
        self.assertEqual(kpi['total_revenue'], 400.0)
        self.assertEqual(kpi['total_cogs'], 600.0)
        self.assertEqual(kpi['gross_profit'], -200.0)
        self.assertEqual(kpi['profit_margin_pct'], -50.0)
        self.assertEqual(kpi['loss_products_count'], 1)
        self.assertEqual(kpi['profitable_products_count'], 0)

    def test_profit_analytics_date_range_and_customer_filtering(self):
        """Filters by date range and stakeholder ID correctly restrict aggregated metrics"""
        import datetime
        now = timezone.now()
        yesterday = now - datetime.timedelta(days=1)
        last_week = now - datetime.timedelta(days=7)

        # Order 1: yesterday, Customer 1
        ord1 = Order.objects.create(
            order_number='SO-FILTER-01',
            stakeholder=self.customer1,
            order_type='SO',
            order_status='Delivered',
            gross_amount=500,
            net_amount=500,
            order_date=yesterday
        )
        OrderItem.objects.create(
            order=ord1,
            product=self.product,
            product_size=self.size8,
            quantity=5,
            price_at_time_of_order=100,
            total=500
        )

        # Order 2: last week, Customer 2
        ord2 = Order.objects.create(
            order_number='SO-FILTER-02',
            stakeholder=self.customer2,
            order_type='SO',
            order_status='Delivered',
            gross_amount=800,
            net_amount=800,
            order_date=last_week
        )
        OrderItem.objects.create(
            order=ord2,
            product=self.product,
            product_size=self.size8,
            quantity=8,
            price_at_time_of_order=100,
            total=800
        )

        # 1. Filter by Customer 1
        res_cust1 = self.client.get(f'/api/inventory/profit-analytics/?stakeholder_id={self.customer1.id}')
        self.assertEqual(res_cust1.status_code, status.HTTP_200_OK)
        self.assertEqual(res_cust1.data['kpi']['total_revenue'], 500.0)

        # 2. Filter by date range (only yesterday)
        res_date = self.client.get(f'/api/inventory/profit-analytics/?start_date={yesterday.date().isoformat()}&end_date={yesterday.date().isoformat()}')
        self.assertEqual(res_date.status_code, status.HTTP_200_OK)
        self.assertEqual(res_date.data['kpi']['total_revenue'], 500.0)






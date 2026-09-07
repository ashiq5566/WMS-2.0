from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from accounts.models import Stakeholder
from inventory.models import Order, Payment, Product, ProductSize

User = get_user_model()

class StakeholderMasterDataTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='admin', password='password123', user_type='admin')
        self.client.force_authenticate(user=self.user)

    def test_stakeholder_creation_and_auto_id(self):
        """Verify Customer and Supplier auto-generate sequential IDs"""
        customer = Stakeholder.objects.create(name='Acme Retail', type='Customer')
        self.assertTrue(customer.stakeholder_id.startswith('CUST-'))
        self.assertTrue(customer.is_active)
        self.assertFalse(customer.is_deleted)

        supplier = Stakeholder.objects.create(name='Global Fabricators', type='Supplier')
        self.assertTrue(supplier.stakeholder_id.startswith('SUPP-'))

        customer2 = Stakeholder.objects.create(name='Beta Stores', type='Customer')
        self.assertNotEqual(customer.stakeholder_id, customer2.stakeholder_id)

    def test_serializer_validation_required_fields(self):
        """Verify name and type validation in serializer"""
        url = '/api/accounts/stakeholders/'

        # Missing name
        res = self.client.post(url, {'type': 'Customer'})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', res.data)

        # Invalid type
        res = self.client.post(url, {'name': 'Test', 'type': 'InvalidType'})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('type', res.data)

    def test_duplicate_email_and_mobile_prevention(self):
        """Verify prevention of duplicate emails and mobile numbers per stakeholder type"""
        url = '/api/accounts/stakeholders/'
        Stakeholder.objects.create(name='Original Customer', type='Customer', email='test@example.com', mobile='9876543210')

        # Attempt duplicate email for Customer
        res = self.client.post(url, {'name': 'Duplicate Email Customer', 'type': 'Customer', 'email': 'test@example.com'})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', res.data)

        # Attempt duplicate mobile for Customer
        res = self.client.post(url, {'name': 'Duplicate Phone Customer', 'type': 'Customer', 'mobile': '9876543210'})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('mobile', res.data)

    def test_duplicate_tax_id_prevention(self):
        """Verify prevention of duplicate Tax ID / GSTIN"""
        url = '/api/accounts/stakeholders/'
        Stakeholder.objects.create(name='GST Org 1', type='Supplier', tax_id='27AAAAA0000A1Z5')

        res = self.client.post(url, {'name': 'GST Org 2', 'type': 'Supplier', 'tax_id': '27AAAAA0000A1Z5'})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('tax_id', res.data)

    def test_referential_integrity_guard_on_deletion(self):
        """Verify that stakeholders with linked orders cannot be hard-deleted"""
        customer = Stakeholder.objects.create(name='Active Buyer', type='Customer')
        Order.objects.create(
            stakeholder=customer,
            order_type='Sales Order',
            order_status='Pending',
            total_amount=1500,
            pending_amount=1500
        )

        url = f'/api/accounts/stakeholders/{customer.id}/'
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', res.data)
        self.assertIn('Cannot permanently delete', res.data['error'])

        # Verify record still exists in DB
        self.assertTrue(Stakeholder.objects.filter(id=customer.id).exists())

    def test_safe_deletion_when_no_active_relations(self):
        """Verify that stakeholder with no references can be deleted cleanly"""
        stakeholder = Stakeholder.objects.create(name='Temporary Stakeholder', type='Customer')
        url = f'/api/accounts/stakeholders/{stakeholder.id}/'
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Stakeholder.objects.filter(id=stakeholder.id).exists())

    def test_status_toggle_action(self):
        """Verify toggle_status soft deactivation endpoint"""
        stakeholder = Stakeholder.objects.create(name='To Deactivate', type='Customer')
        self.assertTrue(stakeholder.is_active)
        self.assertFalse(stakeholder.is_deleted)

        url = f'/api/accounts/stakeholders/{stakeholder.id}/toggle_status/'
        res = self.client.post(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data['is_deleted'])
        self.assertFalse(res.data['is_active'])

        stakeholder.refresh_from_db()
        self.assertTrue(stakeholder.is_deleted)
        self.assertFalse(stakeholder.is_active)

    def test_calculations_and_empty_orders_safety(self):
        """Verify calculations and next_bill_to_clear when stakeholder has 0 orders"""
        stakeholder = Stakeholder.objects.create(name='Zero Bills Customer', type='Customer', opening_balance=500)
        self.assertEqual(stakeholder.total_pending_amount, 500)
        self.assertEqual(stakeholder.total_setteled_amount, 0)
        self.assertEqual(stakeholder.total_orders_count, 0)
        self.assertEqual(stakeholder.total_sales_amount, 0)
        self.assertEqual(stakeholder.total_returns_count, 0)

        # Ensure next_bill_to_clear does not raise AttributeError
        next_bill = stakeholder.next_bill_to_clear
        self.assertEqual(next_bill['pending_amount'], 0)
        self.assertIsNone(next_bill['order_number'])

    def test_stats_kpi_endpoint(self):
        """Verify stats endpoint returns accurate aggregated KPIs"""
        # Create active customer and supplier
        c1 = Stakeholder.objects.create(name='Customer A', type='Customer', opening_balance=1000)
        s1 = Stakeholder.objects.create(name='Supplier A', type='Supplier', opening_balance=2500)
        # Create inactive record
        s2 = Stakeholder.objects.create(name='Inactive Supplier', type='Supplier', is_deleted=True, is_active=False)

        res = self.client.get('/api/accounts/stakeholders/stats/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['total_stakeholders'], 3)
        self.assertEqual(res.data['active_customers'], 1)
        self.assertEqual(res.data['active_suppliers'], 1)
        self.assertEqual(res.data['inactive_records'], 1)
        self.assertEqual(res.data['total_receivable'], 1000)
        self.assertEqual(res.data['total_payable'], 2500)


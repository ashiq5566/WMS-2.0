from django.db import transaction
from django.db.models import functions as db_functions
from django_filters.rest_framework import DjangoFilterBackend
from django.conf import settings
from django.db.models import Sum, F, Q

from rest_framework.decorators import action, api_view
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import viewsets, filters
from rest_framework.filters import OrderingFilter
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from .serializers import *

from inventory.models import *

class OrdersViewSet(viewsets.ModelViewSet):
	queryset = Order.objects.all()
	serializer_class = OrderSerializer
	permission_classes = (IsAuthenticated,)
	filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
	filterset_fields = {
		'stakeholder_id': ['exact'],
  		'date_added': ['exact', 'gte', 'lte'],
        'order_date': ['exact', 'gte', 'lte'],
        'order_type': ['exact'],
        'order_status': ['exact'],
	}
	search_fields = ['id', 'order_number', 'stakeholder__name', 'order_type', 'order_status']
 
	def get_queryset(self):
		queryset = super().get_queryset()
		order_month = self.request.query_params.get('order_month')
		order_status_array = self.request.query_params.getlist('order_status_array[]', [])
		
		if order_month:
			queryset = queryset.annotate(month=db_functions.ExtractMonth('order_date')).filter(month=order_month)
   
		if order_status_array:
			queryset = queryset.filter(order_status__in=order_status_array)
		
		return queryset

	def create(self, request, *args, **kwargs):
		order_data = request.data.get('order')
		items_data = request.data.get('items', [])

		if not order_data:
			return Response({'error': 'Missing order header data'}, status=status.HTTP_400_BAD_REQUEST)
		if not items_data or len(items_data) == 0:
			return Response({'error': 'Order must contain at least one item'}, status=status.HTTP_400_BAD_REQUEST)

		try:
			with transaction.atomic():
				# Auto-generate unique order_number if not provided
				if not order_data.get('order_number'):
					import uuid
					prefix = order_data.get('order_type', 'ORD')
					order_data['order_number'] = f"{prefix}-{uuid.uuid4().hex[:8].upper()}"

				# Create the order
				order_serializer = self.get_serializer(data=order_data)
				order_serializer.is_valid(raise_exception=True)
				order = order_serializer.save()
				
				# Row-level locking & stock validation
				if order.order_type == 'SO':
					for item_data in items_data:
						product_size_id = item_data.get('product_size')
						quantity = int(item_data.get('quantity', 0))
						if quantity <= 0:
							raise ValueError("Item quantity must be greater than zero.")
						
						# Row-level lock on ProductSize
						product_size = ProductSize.objects.select_for_update().get(id=product_size_id)
						if product_size.stock < quantity:
							raise ValueError(
								f"Insufficient stock for {product_size.product.name} (Size {product_size.size}). "
								f"Available: {product_size.stock}, Requested: {quantity}"
							)
				elif order.order_type == 'PO':
					for item_data in items_data:
						product_size_id = item_data.get('product_size')
						quantity = int(item_data.get('quantity', 0))
						if quantity <= 0:
							raise ValueError("Item quantity must be greater than zero.")
						if product_size_id:
							ProductSize.objects.select_for_update().get(id=product_size_id)
				
				# Create the order items
				created_items = []
				for item_data in items_data:
					item_data['order'] = order.id
					item_serializer = OrderItemSerializer(data=item_data)
					item_serializer.is_valid(raise_exception=True)
					created_item = item_serializer.save()
					created_items.append(item_serializer.data)

				response_data = {
					'order': order_serializer.data,
					'items': created_items
				}

				return Response(response_data, status=status.HTTP_201_CREATED)

		except ValueError as e:
			return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
		except Exception as e:
			return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

	def update(self, request, *args, **kwargs):
		partial = kwargs.pop('partial', False)
		instance = self.get_object()
		new_status = request.data.get('order_status')

		# If transitioning to Cancelled from another status, trigger atomic cancellation
		if new_status == 'Cancelled' and instance.order_status != 'Cancelled':
			return self.cancel(request, pk=instance.pk)

		return super().update(request, *args, partial=partial, **kwargs)

	@action(detail=True, methods=['post'])
	def cancel(self, request, pk=None):
		"""
		Cancels an order and reverses its inventory stock impact atomically.
		For SO: restores decremented stock to ProductSize and logs an ADJUSTMENT StockMovement.
		For PO: removes added stock from ProductSize and logs an ADJUSTMENT StockMovement.
		"""
		order = self.get_object()
		if order.order_status == 'Cancelled':
			return Response({'error': 'Order is already cancelled.'}, status=status.HTTP_400_BAD_REQUEST)

		try:
			with transaction.atomic():
				# Lock and reverse stock for each order item
				for item in order.items.select_related('product_size', 'product').all():
					if item.product_size:
						ps = ProductSize.objects.select_for_update().get(id=item.product_size.id)
						if order.order_type == 'SO':
							# SO had decreased stock, now restore it
							ps.stock += item.quantity
							ps.save()
							StockMovement.objects.create(
								product_size=ps,
								order=order,
								movement_type='ADJUSTMENT',
								quantity=item.quantity,
								reference=order.order_number,
								notes=f"Restored stock from cancelled SO {order.order_number}"
							)
						elif order.order_type == 'PO':
							# PO had increased stock, check if stock was already consumed
							if ps.stock < item.quantity:
								raise ValueError(
									f"Cannot cancel PO: {ps.product.name} (Size {ps.size}) "
									f"current stock ({ps.stock}) is less than order quantity ({item.quantity})."
								)
							ps.stock -= item.quantity
							ps.save()
							StockMovement.objects.create(
								product_size=ps,
								order=order,
								movement_type='ADJUSTMENT',
								quantity=-item.quantity,
								reference=order.order_number,
								notes=f"Reversed stock from cancelled PO {order.order_number}"
							)

				order.order_status = 'Cancelled'
				order.pending_amount = 0
				order.save()

				return Response({
					'status': 'Order cancelled successfully',
					'order': self.get_serializer(order).data
				}, status=status.HTTP_200_OK)
		except ValueError as e:
			return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
		except Exception as e:
			return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
	
	@action(detail=False, methods=['get'])
	def get_total_by_stakeholders(self, request):
		stakeholder_ids = request.query_params.getlist('stakeholder_ids[]')
		
		if stakeholder_ids:
			# Filter orders by the list of stakeholder IDs and aggregate the total amount per stakeholder
			data = (
				self.queryset.filter(stakeholder_id__in=stakeholder_ids)
				.values(stakeholder_name=F('stakeholder__name'))
				.annotate(total_amount=Sum('pending_amount'))
				.values('stakeholder_name', 'total_amount')
			)
			# Format response as required
			response_data = [{'stakeholder': item['stakeholder_name'], 'amount': item['total_amount']} for item in data]
			
			return Response(response_data, status=status.HTTP_200_OK)
		
		return Response({"error": "No stakeholder IDs provided"}, status=status.HTTP_400_BAD_REQUEST)
class OrderItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    permission_classes = (IsAuthenticated, )
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_fields = {
        'order_id': ['exact'],
    }
    
class ProductViewSet(viewsets.ModelViewSet):
	queryset = Product.objects.all()
	permission_classes = (AllowAny, )
	filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
	search_fields = ['product_id', 'name', 'status']
 
	def get_serializer_class(self):
		if self.action in ["create", "update", "partial_update"]:
			return ProductCreateSerializer
		return ProductSerializer

    
class ReturnViewSet(viewsets.ModelViewSet):
	queryset = Return.objects.all().select_related('original_order', 'original_order__stakeholder').prefetch_related('items__product', 'items__product_size')
	serializer_class = ReturnSerializer
	permission_classes = (IsAuthenticated, )
	filter_backends = (DjangoFilterBackend, filters.SearchFilter, OrderingFilter)
	filterset_fields = {
		'original_order': ['exact'],
		'date_added': ['exact', 'gte', 'lte'],
		'return_type': ['exact'],
		'return_status': ['exact', 'in'],
		'original_order__stakeholder': ['exact']
	}
	search_fields = ['id', 'original_order__order_number', 'original_order__stakeholder__name', 'return_type', 'return_status']

	def create(self, request, *args, **kwargs):
		return_data = request.data.get('return')
		items_data = request.data.get('items', [])

		if not return_data:
			return Response({'error': 'Return payload is required.'}, status=status.HTTP_400_BAD_REQUEST)
		if not items_data:
			return Response({'error': 'At least one return item is required.'}, status=status.HTTP_400_BAD_REQUEST)

		try:
			with transaction.atomic():
				# 1. Lock and validate the original order
				original_order_id = return_data.get('original_order')
				if not original_order_id:
					return Response({'error': 'Original order ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

				try:
					original_order = Order.objects.select_for_update().get(pk=original_order_id)
				except Order.DoesNotExist:
					return Response({'error': f'Order {original_order_id} does not exist.'}, status=status.HTTP_404_NOT_FOUND)

				if original_order.order_status == 'Cancelled':
					return Response({'error': 'Cannot process return for a cancelled order.'}, status=status.HTTP_400_BAD_REQUEST)

				if original_order.order_status not in ['Issued', 'Delivered', 'Recieved', 'Closed']:
					return Response({
						'error': f'Cannot process return for order with status "{original_order.order_status}". Returns require issued, delivered, or completed orders.'
					}, status=status.HTTP_400_BAD_REQUEST)

				return_type = return_data.get('return_type')
				if not return_type:
					return_type = 'SR' if original_order.order_type == 'SO' else 'PR'
					return_data['return_type'] = return_type

				if not return_data.get('return_status'):
					return_data['return_status'] = 'Completed'

				# Prevent duplicate item lines in return manifest
				seen_sizes = set()
				for item_data in items_data:
					product_size_id = item_data.get('product_size')
					if product_size_id in seen_sizes:
						return Response({'error': f'Duplicate product variant (ID: {product_size_id}) detected in return lines.'}, status=status.HTTP_400_BAD_REQUEST)
					seen_sizes.add(product_size_id)

				# 2. Validate items against original order items & cumulative quantities
				for item_data in items_data:
					product_size_id = item_data.get('product_size')
					qty = int(item_data.get('quantity', 0))

					if qty <= 0:
						return Response({'error': 'Return quantity must be greater than zero.'}, status=status.HTTP_400_BAD_REQUEST)

					if not product_size_id:
						return Response({'error': 'Each return item must specify a product_size.'}, status=status.HTTP_400_BAD_REQUEST)

					# Check order item exists in original order
					order_item = OrderItem.objects.filter(order=original_order, product_size_id=product_size_id).first()
					if not order_item:
						return Response({
							'error': f'Product variant (ID: {product_size_id}) was not part of original order {original_order.order_number}.'
						}, status=status.HTTP_400_BAD_REQUEST)

					# Calculate cumulative returned quantity for this order and product_size
					already_returned = ReturnItem.objects.filter(
						return_order__original_order=original_order,
						return_order__return_status__in=['Approved', 'Processed', 'Completed'],
						product_size_id=product_size_id
					).aggregate(total=Sum('quantity'))['total'] or 0

					remaining_returnable = order_item.quantity - already_returned
					if qty > remaining_returnable:
						variant_name = f"Size {order_item.product_size.size}" if order_item.product_size else "item"
						return Response({
							'error': f'Cannot return {qty} units of {variant_name}. Max returnable: {remaining_returnable} (Ordered: {order_item.quantity}, Already returned: {already_returned}).'
						}, status=status.HTTP_400_BAD_REQUEST)

					# If Purchase Return (PR) and approved/completed status, verify current stock sufficiency on product_size
					if return_type == 'PR' and return_data.get('return_status') in ['Approved', 'Processed', 'Completed']:
						ps = ProductSize.objects.select_for_update().get(pk=product_size_id)
						if ps.stock < qty:
							return Response({
								'error': f'Insufficient warehouse stock for {ps.product.name} (Size {ps.size}). Available: {ps.stock}, Attempted return: {qty}.'
							}, status=status.HTTP_400_BAD_REQUEST)

				# 3. Create the Return record
				return_serializer = self.get_serializer(data=return_data)
				return_serializer.is_valid(raise_exception=True)
				order = return_serializer.save()

				# 4. Create the ReturnItem records
				created_items = []
				for item_data in items_data:
					item_data['return_order'] = order.id
					# Ensure product is populated if missing but product_size is present
					if not item_data.get('product') and item_data.get('product_size'):
						ps = ProductSize.objects.get(pk=item_data['product_size'])
						item_data['product'] = ps.product_id

					item_serializer = ReturnItemSerializer(data=item_data)
					item_serializer.is_valid(raise_exception=True)
					created_item = item_serializer.save()
					created_items.append(item_serializer.data)

				response_data = {
					'return': return_serializer.data,
					'items': created_items
				}

				return Response(response_data, status=status.HTTP_201_CREATED)

		except Exception as e:
			return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

	@action(detail=True, methods=['post'])
	def approve(self, request, pk=None):
		try:
			with transaction.atomic():
				return_obj = Return.objects.select_for_update().get(pk=pk)
				if return_obj.return_status in ['Approved', 'Processed', 'Completed']:
					return Response({'error': f'Return is already {return_obj.return_status}.'}, status=status.HTTP_400_BAD_REQUEST)

				if return_obj.return_status == 'Rejected':
					return Response({'error': 'Cannot approve a rejected return.'}, status=status.HTTP_400_BAD_REQUEST)

				# Check PR warehouse stock before approving
				if return_obj.return_type == 'PR':
					for item in return_obj.items.all():
						if item.product_size:
							ps = ProductSize.objects.select_for_update().get(pk=item.product_size.pk)
							if ps.stock < item.quantity:
								return Response({
									'error': f'Insufficient warehouse stock for {ps.product.name} (Size {ps.size}). Available: {ps.stock}, Required: {item.quantity}.'
								}, status=status.HTTP_400_BAD_REQUEST)

				return_obj.return_status = 'Completed'
				return_obj.save()

				# Adjust items
				for item in return_obj.items.all():
					if item.product_size:
						if return_obj.return_type == 'SR':
							if item.condition in ['Good', 'Wrong Item']:
								item.product_size.stock += item.quantity
								item.product_size.save()
								qty_delta = item.quantity
							else:
								qty_delta = 0
							movement_type = 'RETURN_SALE'
						elif return_obj.return_type == 'PR':
							item.product_size.stock -= item.quantity
							item.product_size.save()
							movement_type = 'RETURN_PURCHASE'
							qty_delta = -item.quantity

						StockMovement.objects.create(
							product_size=item.product_size,
							order=return_obj.original_order,
							movement_type=movement_type,
							quantity=qty_delta,
							reference=return_obj.original_order.order_number,
							notes=f"Return {return_obj.return_type} ({item.condition}) approved - {item.reason or 'Processed'}"
						)

				return Response(ReturnSerializer(return_obj).data, status=status.HTTP_200_OK)
		except Exception as e:
			return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    
class ReturnItemViewSet(viewsets.ModelViewSet):
	queryset = ReturnItem.objects.all()
	serializer_class = ReturnItemSerializer
	permission_classes = (IsAuthenticated, )
	filter_backends = (DjangoFilterBackend, OrderingFilter)
	filterset_fields = {
		'return_order': ['exact'],
	}
  
class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all().order_by('-payment_date', '-id')
    serializer_class = PaymentSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, OrderingFilter)
    filterset_fields = {
        'order_id': ['exact'],
        'order__stakeholder_id': ['exact'],
        'order__order_type': ['exact'],
        'company__id': ['exact'],
        'payment_type': ['exact'],
        'status': ['exact'],
        'payment_method': ['exact'],
        'payment_date': ['exact', 'gte', 'lte'],
    }
    search_fields = ['id', 'payment_number', 'reference', 'payment_method', 'payment_type', 'status', 'order__order_number', 'company__name', 'notes']
    ordering_fields = ['payment_date', 'amount', 'id', 'payment_number']
    ordering = ['-payment_date', '-id']

    def get_queryset(self):
        queryset = super().get_queryset()
        order_month = self.request.query_params.get('order_month')

        if order_month:
            queryset = queryset.annotate(month=db_functions.ExtractMonth('payment_date')).filter(month=order_month)

        return queryset

    @action(detail=False, methods=['get'])
    def financial_summary(self, request):
        """
        Executive-level WMS financial health and cash flow analytics
        """
        from django.utils import timezone
        import datetime

        now = timezone.now()
        start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        thirty_days_ago = now - datetime.timedelta(days=30)

        # Inflows (Money Received) & Outflows (Money Paid)
        total_received = Payment.objects.filter(payment_type='INBOUND', status='Completed').aggregate(total=Sum('amount'))['total'] or 0
        total_paid = Payment.objects.filter(payment_type='OUTBOUND', status='Completed').aggregate(total=Sum('amount'))['total'] or 0
        total_refunds = Payment.objects.filter(payment_type='REFUND', status='Completed').aggregate(total=Sum('amount'))['total'] or 0
        net_cash_flow = total_received - total_paid - total_refunds

        # Sales Revenue & Purchase Expense
        total_sales_revenue = Order.objects.filter(order_type='SO').aggregate(total=Sum('total_amount'))['total'] or 0
        total_purchase_expense = Order.objects.filter(order_type='PO').aggregate(total=Sum('total_amount'))['total'] or 0

        # Outstanding Balances
        so_pending = Order.objects.filter(order_type='SO', pending_amount__gt=0).aggregate(total=Sum('pending_amount'))['total'] or 0
        cust_ob = Stakeholder.objects.filter(type='Customer', is_deleted=False).aggregate(total=Sum('opening_balance'))['total'] or 0
        outstanding_receivables = so_pending + (cust_ob or 0)

        po_pending = Order.objects.filter(order_type='PO', pending_amount__gt=0).aggregate(total=Sum('pending_amount'))['total'] or 0
        supp_ob = Stakeholder.objects.filter(type='Supplier', is_deleted=False).aggregate(total=Sum('opening_balance'))['total'] or 0
        outstanding_payables = po_pending + (supp_ob or 0)

        # Overdue Balances (> 30 days old)
        overdue_receivables = Order.objects.filter(order_type='SO', pending_amount__gt=0, date_added__lt=thirty_days_ago).aggregate(total=Sum('pending_amount'))['total'] or 0
        overdue_payables = Order.objects.filter(order_type='PO', pending_amount__gt=0, date_added__lt=thirty_days_ago).aggregate(total=Sum('pending_amount'))['total'] or 0

        # Today's Collections & Disbursements
        today_collections = Payment.objects.filter(payment_type='INBOUND', status='Completed', payment_date__gte=start_of_today).aggregate(total=Sum('amount'))['total'] or 0
        today_disbursements = Payment.objects.filter(payment_type='OUTBOUND', status='Completed', payment_date__gte=start_of_today).aggregate(total=Sum('amount'))['total'] or 0

        # Order Status breakdown
        paid_orders_count = Order.objects.filter(order_status='Closed').count()
        partially_paid_orders_count = Order.objects.filter(order_status='Issued', pending_amount__lt=F('total_amount'), pending_amount__gt=0).count()
        unpaid_orders_count = Order.objects.filter(order_status='Issued', pending_amount=F('total_amount')).count()
        overdue_orders_count = Order.objects.filter(order_status='Issued', pending_amount__gt=0, date_added__lt=thirty_days_ago).count()

        # Monthly Trends (last 6 months)
        monthly_trends = []
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        for i in range(5, -1, -1):
            # Compute month index
            target_month = (now.month - i - 1) % 12 + 1
            target_year = now.year if (now.month - i) > 0 else now.year - 1
            label = f"{month_names[target_month - 1]} {str(target_year)[2:]}"

            inflow = Payment.objects.filter(
                payment_type='INBOUND',
                status='Completed',
                payment_date__year=target_year,
                payment_date__month=target_month
            ).aggregate(total=Sum('amount'))['total'] or 0

            outflow = Payment.objects.filter(
                payment_type='OUTBOUND',
                status='Completed',
                payment_date__year=target_year,
                payment_date__month=target_month
            ).aggregate(total=Sum('amount'))['total'] or 0

            monthly_trends.append({
                'month': label,
                'inflows': inflow,
                'outflows': outflow,
                'net': inflow - outflow,
            })

        # Settlement Breakdown & Percentages
        sales_collected = max(0, total_sales_revenue - so_pending)
        sales_settlement_pct = round((sales_collected / total_sales_revenue) * 100, 1) if total_sales_revenue > 0 else 100.0

        purchase_disbursed = max(0, total_purchase_expense - po_pending)
        purchase_settlement_pct = round((purchase_disbursed / total_purchase_expense) * 100, 1) if total_purchase_expense > 0 else 100.0

        settlement_breakdown = {
            'sales_total_billed': total_sales_revenue,
            'sales_pending': so_pending,
            'sales_collected': sales_collected,
            'sales_settlement_pct': sales_settlement_pct,
            'purchase_total_billed': total_purchase_expense,
            'purchase_pending': po_pending,
            'purchase_disbursed': purchase_disbursed,
            'purchase_settlement_pct': purchase_settlement_pct,
        }

        return Response({
            'total_revenue': total_sales_revenue,
            'total_purchase_expense': total_purchase_expense,
            'total_received': total_received,
            'total_paid': total_paid,
            'total_refunds': total_refunds,
            'net_cash_flow': net_cash_flow,
            'outstanding_receivables': outstanding_receivables,
            'outstanding_payables': outstanding_payables,
            'overdue_receivables': overdue_receivables,
            'overdue_payables': overdue_payables,
            'today_collections': today_collections,
            'today_disbursements': today_disbursements,
            'sales_settlement_pct': sales_settlement_pct,
            'purchase_settlement_pct': purchase_settlement_pct,
            'settlement_breakdown': settlement_breakdown,
            'order_status_breakdown': {
                'paid_orders': paid_orders_count,
                'partially_paid_orders': partially_paid_orders_count,
                'unpaid_orders': unpaid_orders_count,
                'overdue_orders': overdue_orders_count,
            },
            'monthly_trends': monthly_trends,
        }, status=status.HTTP_200_OK)


class CartViewSet(viewsets.ModelViewSet):

    # permission_classes = [IsAuthenticated]
    queryset = Cart.objects.all()
    serializer_class = CartSerializer

    def get_queryset(self):
        user = User.objects.first()  # TEMP
        queryset = Cart.objects.filter(user=user)
        return queryset

    def create(self, request):
        product_id = request.data.get("product_id")
        size_id = request.data.get("size_id")
        quantity = int(request.data.get("quantity", 1))

        if not product_id or not size_id:
            return Response(
                {"error": "Product ID and Size ID are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate product
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response(
                {"error": "Product not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Validate size
        try:
            size = ProductSize.objects.get(id=size_id, product=product)
        except ProductSize.DoesNotExist:
            return Response(
                {"error": "Invalid size for this product"},
                status=status.HTTP_404_NOT_FOUND
            )

        # TEMP (replace later with request.user)
        user = User.objects.first()

        cart, _ = Cart.objects.get_or_create(user=user)

        # Check if same product + same size already exists
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            size=size
        )

        if not created:
            cart_item.quantity += quantity
        else:
            cart_item.quantity = quantity

        cart_item.save()

        return Response(
            {
                "message": "Product added to cart successfully",
                "product": product.name,
                "size": size.size,
                "quantity": cart_item.quantity,
            },
            status=status.HTTP_200_OK
        )


class CartItemViewSet(viewsets.ModelViewSet):
    # permission_classes = [IsAuthenticated]
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer


class ProfitAnalyticsViewSet(viewsets.ViewSet):
    """
    Dedicated Profit Tracking & Margin Analytics API
    Provides real-time profitability metrics based on purchase cost vs. selling price,
    sales volume, and sales return deductions.
    """
    permission_classes = (IsAuthenticated,)

    def list(self, request):
        from django.utils import timezone
        import datetime

        now = timezone.now()
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        date_range = request.query_params.get('date_range')
        stakeholder_id = request.query_params.get('stakeholder_id')
        product_id = request.query_params.get('product_id')
        search_query = request.query_params.get('search', '').strip()

        # Handle preset date ranges
        if date_range == 'today':
            start_date = now.date().isoformat()
            end_date = now.date().isoformat()
        elif date_range == 'this_month':
            start_date = now.replace(day=1).date().isoformat()
            end_date = now.date().isoformat()
        elif date_range == 'last_month':
            first_this_month = now.replace(day=1)
            last_month_end = first_this_month - datetime.timedelta(days=1)
            last_month_start = last_month_end.replace(day=1)
            start_date = last_month_start.date().isoformat()
            end_date = last_month_end.date().isoformat()
        elif date_range == 'this_year':
            start_date = now.replace(month=1, day=1).date().isoformat()
            end_date = now.date().isoformat()

        # 1. Base Query: Only fulfilled / valid Sales Orders (exclude Cancelled and Draft)
        orders_qs = Order.objects.filter(order_type='SO').exclude(order_status__in=['Cancelled', 'Draft'])

        if start_date:
            orders_qs = orders_qs.filter(
                Q(order_date__date__gte=start_date) | Q(order_date__isnull=True, date_added__date__gte=start_date)
            )
        if end_date:
            orders_qs = orders_qs.filter(
                Q(order_date__date__lte=end_date) | Q(order_date__isnull=True, date_added__date__lte=end_date)
            )
        if stakeholder_id:
            orders_qs = orders_qs.filter(stakeholder_id=stakeholder_id)

        # 2. Fetch Order Items
        items_qs = OrderItem.objects.filter(order__in=orders_qs).select_related(
            'order', 'product', 'product_size', 'order__stakeholder'
        )
        if product_id:
            items_qs = items_qs.filter(product_id=product_id)

        # 3. Fetch Completed Sales Returns associated with these orders
        returns_qs = Return.objects.filter(
            original_order__in=orders_qs,
            return_type='SR',
            return_status__in=['Approved', 'Processed', 'Completed']
        )
        return_items_qs = ReturnItem.objects.filter(return_order__in=returns_qs).select_related(
            'return_order', 'return_order__original_order', 'product', 'product_size'
        )
        if product_id:
            return_items_qs = return_items_qs.filter(product_id=product_id)

        # Helper for unit purchase cost
        def resolve_unit_cost(prod, size_obj):
            if size_obj and size_obj.price_at_time_of_purchase is not None:
                return float(size_obj.price_at_time_of_purchase)
            if prod and prod.price_at_time_of_purchase is not None:
                return float(prod.price_at_time_of_purchase)
            return 0.0

        # Build returns map by (product_id, size_id) and by order_id
        returns_by_sku = {}
        returns_by_order = {}
        total_returned_revenue = 0.0
        total_returned_cogs = 0.0
        total_returned_units = 0

        for r_item in return_items_qs:
            p_id = r_item.product_id
            s_id = r_item.product_size_id
            sku_key = (p_id, s_id)
            ord_id = r_item.return_order.original_order_id

            qty = r_item.quantity or 0
            price_ret = float(r_item.price_at_return or 0)
            ret_rev = float(r_item.total) if r_item.total is not None else (qty * price_ret)
            unit_cost = resolve_unit_cost(r_item.product, r_item.product_size)
            ret_cogs = qty * unit_cost

            total_returned_revenue += ret_rev
            total_returned_cogs += ret_cogs
            total_returned_units += qty

            if sku_key not in returns_by_sku:
                returns_by_sku[sku_key] = {'qty': 0, 'revenue': 0.0, 'cogs': 0.0}
            returns_by_sku[sku_key]['qty'] += qty
            returns_by_sku[sku_key]['revenue'] += ret_rev
            returns_by_sku[sku_key]['cogs'] += ret_cogs

            if ord_id not in returns_by_order:
                returns_by_order[ord_id] = {'qty': 0, 'revenue': 0.0, 'cogs': 0.0}
            returns_by_order[ord_id]['qty'] += qty
            returns_by_order[ord_id]['revenue'] += ret_rev
            returns_by_order[ord_id]['cogs'] += ret_cogs

        # 4. Aggregate by Product / SKU
        sku_map = {}
        for item in items_qs:
            p_id = item.product_id
            s_id = item.product_size_id
            sku_key = (p_id, s_id)

            qty = item.quantity or 0
            unit_sell_price = float(item.price_at_time_of_order or 0)
            rev = float(item.total) if item.total is not None else (qty * unit_sell_price)
            unit_cost = resolve_unit_cost(item.product, item.product_size)
            cogs = qty * unit_cost

            if sku_key not in sku_map:
                sku_map[sku_key] = {
                    'product_id': f"PR{item.product.pk}",
                    'raw_product_id': item.product.id,
                    'product_name': item.product.name,
                    'size_id': s_id,
                    'size': item.product_size.size if item.product_size else 'Standard',
                    'unit': item.product.unit or 'Pieces',
                    'gross_quantity': 0,
                    'gross_revenue': 0.0,
                    'gross_cogs': 0.0,
                    'unit_cost': unit_cost,
                    'selling_price': unit_sell_price,
                }
            sku_map[sku_key]['gross_quantity'] += qty
            sku_map[sku_key]['gross_revenue'] += rev
            sku_map[sku_key]['gross_cogs'] += cogs

        # Process by_product array with returns applied
        by_product = []
        for sku_key, sku_data in sku_map.items():
            ret_data = returns_by_sku.get(sku_key, {'qty': 0, 'revenue': 0.0, 'cogs': 0.0})
            net_qty = sku_data['gross_quantity'] - ret_data['qty']
            net_rev = max(0.0, sku_data['gross_revenue'] - ret_data['revenue'])
            net_cogs = max(0.0, sku_data['gross_cogs'] - ret_data['cogs'])
            gross_profit = net_rev - net_cogs
            margin_pct = round((gross_profit / net_rev) * 100, 1) if net_rev > 0 else 0.0

            row = {
                'product_id': sku_data['product_id'],
                'raw_product_id': sku_data['raw_product_id'],
                'product_name': sku_data['product_name'],
                'size_id': sku_data['size_id'],
                'size': sku_data['size'],
                'unit': sku_data['unit'],
                'units_sold': net_qty,
                'units_returned': ret_data['qty'],
                'avg_selling_price': round(sku_data['selling_price'], 2),
                'cost_price': round(sku_data['unit_cost'], 2),
                'total_revenue': round(net_rev, 2),
                'total_cogs': round(net_cogs, 2),
                'gross_profit': round(gross_profit, 2),
                'profit_margin_pct': margin_pct,
                'is_profitable': gross_profit >= 0,
            }

            # Search filter on product level
            if search_query:
                q_lower = search_query.lower()
                matches = (
                    q_lower in row['product_name'].lower() or
                    q_lower in row['product_id'].lower() or
                    q_lower in str(row['size']).lower()
                )
                if not matches:
                    continue

            by_product.append(row)

        by_product.sort(key=lambda x: x['gross_profit'], reverse=True)

        # 5. Aggregate by Order
        order_map = {}
        for item in items_qs:
            ord_obj = item.order
            ord_id = ord_obj.id

            qty = item.quantity or 0
            unit_sell_price = float(item.price_at_time_of_order or 0)
            rev = float(item.total) if item.total is not None else (qty * unit_sell_price)
            unit_cost = resolve_unit_cost(item.product, item.product_size)
            cogs = qty * unit_cost

            if ord_id not in order_map:
                order_map[ord_id] = {
                    'order_id': ord_id,
                    'order_number': ord_obj.order_number or f"SO-{ord_id}",
                    'order_date': (ord_obj.order_date or ord_obj.date_added).isoformat() if (ord_obj.order_date or ord_obj.date_added) else None,
                    'stakeholder_name': ord_obj.stakeholder.name if ord_obj.stakeholder else 'Direct Customer',
                    'order_status': ord_obj.order_status,
                    'items_count': 0,
                    'gross_revenue': 0.0,
                    'gross_cogs': 0.0,
                }
            order_map[ord_id]['items_count'] += 1
            order_map[ord_id]['gross_revenue'] += rev
            order_map[ord_id]['gross_cogs'] += cogs

        by_order = []
        for ord_id, ord_data in order_map.items():
            ret_data = returns_by_order.get(ord_id, {'qty': 0, 'revenue': 0.0, 'cogs': 0.0})
            net_rev = max(0.0, ord_data['gross_revenue'] - ret_data['revenue'])
            net_cogs = max(0.0, ord_data['gross_cogs'] - ret_data['cogs'])
            gross_profit = net_rev - net_cogs
            margin_pct = round((gross_profit / net_rev) * 100, 1) if net_rev > 0 else 0.0

            row = {
                'order_id': ord_data['order_id'],
                'order_number': ord_data['order_number'],
                'order_date': ord_data['order_date'],
                'stakeholder_name': ord_data['stakeholder_name'],
                'order_status': ord_data['order_status'],
                'items_count': ord_data['items_count'],
                'total_revenue': round(net_rev, 2),
                'total_cogs': round(net_cogs, 2),
                'gross_profit': round(gross_profit, 2),
                'profit_margin_pct': margin_pct,
                'is_profitable': gross_profit >= 0,
            }

            if search_query:
                q_lower = search_query.lower()
                matches = (
                    q_lower in row['order_number'].lower() or
                    q_lower in row['stakeholder_name'].lower()
                )
                if not matches:
                    continue

            by_order.append(row)

        by_order.sort(key=lambda x: x['order_date'] or '', reverse=True)

        # 6. Overall Summary KPIs
        total_gross_rev = sum(item['gross_revenue'] for item in sku_map.values())
        total_gross_cogs = sum(item['gross_cogs'] for item in sku_map.values())
        net_total_revenue = max(0.0, total_gross_rev - total_returned_revenue)
        net_total_cogs = max(0.0, total_gross_cogs - total_returned_cogs)
        net_gross_profit = net_total_revenue - net_total_cogs
        overall_margin_pct = round((net_gross_profit / net_total_revenue) * 100, 1) if net_total_revenue > 0 else 0.0

        total_net_units = sum(p['units_sold'] for p in by_product)
        profitable_count = sum(1 for p in by_product if p['is_profitable'])
        loss_count = sum(1 for p in by_product if not p['is_profitable'])

        # 7. Monthly Trends (last 6 months)
        monthly_trends = []
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        for i in range(5, -1, -1):
            target_month = (now.month - i - 1) % 12 + 1
            target_year = now.year if (now.month - i) > 0 else now.year - 1
            label = f"{month_names[target_month - 1]} {str(target_year)[2:]}"

            m_orders = Order.objects.filter(
                order_type='SO'
            ).filter(
                Q(order_date__year=target_year, order_date__month=target_month) |
                Q(order_date__isnull=True, date_added__year=target_year, date_added__month=target_month)
            ).exclude(order_status__in=['Cancelled', 'Draft'])

            m_items = OrderItem.objects.filter(order__in=m_orders).select_related('product', 'product_size')
            m_rev = 0.0
            m_cogs = 0.0
            for it in m_items:
                q = it.quantity or 0
                pr = float(it.price_at_time_of_order or 0)
                m_rev += float(it.total) if it.total is not None else (q * pr)
                c = resolve_unit_cost(it.product, it.product_size)
                m_cogs += q * c

            # Deduct returns in this month
            m_returns = Return.objects.filter(
                original_order__in=m_orders,
                return_type='SR',
                return_status__in=['Approved', 'Processed', 'Completed']
            )
            m_ret_items = ReturnItem.objects.filter(return_order__in=m_returns).select_related('product', 'product_size')
            for r in m_ret_items:
                rq = r.quantity or 0
                rp = float(r.price_at_return or 0)
                m_rev = max(0.0, m_rev - (float(r.total) if r.total is not None else rq * rp))
                m_cogs = max(0.0, m_cogs - (rq * resolve_unit_cost(r.product, r.product_size)))

            m_profit = m_rev - m_cogs
            m_margin = round((m_profit / m_rev) * 100, 1) if m_rev > 0 else 0.0

            monthly_trends.append({
                'month': label,
                'revenue': round(m_rev, 2),
                'cogs': round(m_cogs, 2),
                'gross_profit': round(m_profit, 2),
                'margin_pct': m_margin,
            })

        return Response({
            'kpi': {
                'total_revenue': round(net_total_revenue, 2),
                'total_cogs': round(net_total_cogs, 2),
                'gross_profit': round(net_gross_profit, 2),
                'profit_margin_pct': overall_margin_pct,
                'total_orders_count': len(by_order),
                'total_items_sold': total_net_units,
                'total_returned_units': total_returned_units,
                'total_returned_revenue': round(total_returned_revenue, 2),
                'profitable_products_count': profitable_count,
                'loss_products_count': loss_count,
            },
            'by_product': by_product,
            'by_order': by_order,
            'monthly_trends': monthly_trends,
        }, status=status.HTTP_200_OK)
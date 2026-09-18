from django.db import transaction
from django.db.models import functions as db_functions
from django_filters.rest_framework import DjangoFilterBackend
from django.conf import settings
from django.db.models import Sum, F

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
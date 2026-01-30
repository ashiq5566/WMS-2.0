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

		try:
			with transaction.atomic():
				# Create the order
				order_serializer = self.get_serializer(data=order_data)
				order_serializer.is_valid(raise_exception=True)
				order = order_serializer.save()
				# Create the order items
				print("Order saved", order, items_data)
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
	queryset = Return.objects.all()
	serializer_class = ReturnSerializer
	permission_classes = (IsAuthenticated, )
	filter_backends = (DjangoFilterBackend, OrderingFilter)
	filterset_fields = {
		'original_order': ['exact'],
		'date_added': ['exact', 'gte', 'lte'],
		'return_type': ['exact'],
		'original_order__stakeholder': ['exact']
	}

	def create(self, request, *args, **kwargs):
		return_data = request.data.get('return')
		items_data = request.data.get('items', [])
		
		try:
			with transaction.atomic():
				print(return_data, items_data)
				# Create the order
				return_serializer = self.get_serializer(data=return_data)
				return_serializer.is_valid(raise_exception=True)
				order = return_serializer.save()
				# Create the order items
				created_items = []
				for item_data in items_data:
					item_data['return_order'] = order.id
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
    
    
class ReturnItemViewSet(viewsets.ModelViewSet):
	queryset = ReturnItem.objects.all()
	serializer_class = ReturnItemSerializer
	permission_classes = (IsAuthenticated, )
	filter_backends = (DjangoFilterBackend, OrderingFilter)
	filterset_fields = {
		'return_order': ['exact'],
	}
  
class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_fields = {
        'order_id': ['exact'],
        'order__stakeholder_id': ['exact'],
        'order__order_type': ['exact'],
        'company__id': ['exact'],
        'payment_date': ['exact', 'gte', 'lte'],
    }

    def get_queryset(self):
        queryset = super().get_queryset()
        order_month = self.request.query_params.get('order_month')

        if order_month:
            queryset = queryset.annotate(month=db_functions.ExtractMonth('payment_date')).filter(month=order_month)

        return queryset
    
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
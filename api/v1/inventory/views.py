from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from django.conf import settings
from django.db.models import Sum, F

from rest_framework.decorators import action
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import viewsets, filters
from rest_framework.filters import OrderingFilter
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
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
	}
	search_fields = ['id', 'order_number', 'stakeholder__name', 'order_type', 'order_status']

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
	serializer_class = ProductSerializer
	permission_classes = (IsAuthenticated, )
	filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
	search_fields = ['product_id', 'name', 'status']

    
class ReturnViewSet(viewsets.ModelViewSet):
	queryset = Return.objects.all()
	serializer_class = ReturnSerializer
	permission_classes = (IsAuthenticated, )
	filter_backends = (DjangoFilterBackend, OrderingFilter)
	filterset_fields = {
			'original_order': ['exact'],
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
    permission_classes = (IsAuthenticated, )
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_fields = {
		'order_id': ['exact'],
		'order__stakeholder_id': ['exact'],
  		'payment_date': ['exact', 'gte', 'lte'],
  
	}
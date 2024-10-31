from rest_framework import viewsets
from django.db import transaction
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
from .serializers import OrderSerializer, ProductSerializer, OrderItemSerializer, ReturnSerializer, ReturnItemSerializer

from inventory.models import Order, OrderItem, Product, Return, ReturnItem

class OrdersViewSet(viewsets.ModelViewSet):
	queryset = Order.objects.all()
	serializer_class = OrderSerializer
	permission_classes = (IsAuthenticated,)

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
	
class OrderItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    permission_classes = (IsAuthenticated, )
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_fields = {
        'order__id': ['exact'],
    }
    
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = (IsAuthenticated, )
    
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
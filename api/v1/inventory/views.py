from rest_framework import viewsets
from django.db import transaction
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
from .serializers import OrderSerializer, ProductSerializer, OrderItemSerializer

from inventory.models import Order, OrderItem, Product

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
    
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = (IsAuthenticated, )
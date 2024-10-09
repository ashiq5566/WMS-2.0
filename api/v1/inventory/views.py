from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate, login
from django.conf import settings
from importlib import import_module
from .serializers import OrderSerializer, ProductSerializer, OrderItemSerializer

from inventory.models import Order, OrderItem, Product
class OrdersViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = (IsAuthenticated, )
    
class OrderItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    permission_classes = (IsAuthenticated, )
    
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = (IsAuthenticated, )
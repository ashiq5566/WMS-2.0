from django.urls import path
from rest_framework import routers
from .views import OrdersViewSet, OrderItemViewSet, ProductViewSet


router = routers.SimpleRouter()
# router.register(r'login', LoginView)
router.register(r'orders', OrdersViewSet)
router.register(r'order-items', OrderItemViewSet)
router.register(r'products', ProductViewSet)
urlpatterns = router.urls

urlpatterns += [
]
from django.urls import path
from rest_framework import routers
from .views import OrdersViewSet, OrderItemViewSet, ProductViewSet, ReturnViewSet, ReturnItemViewSet, PaymentViewSet, add_to_cart


router = routers.SimpleRouter()
# router.register(r'login', LoginView)
router.register(r'orders', OrdersViewSet)
router.register(r'order-items', OrderItemViewSet)
router.register(r'products', ProductViewSet)
router.register(r'returns', ReturnViewSet)
router.register(r'return-items', ReturnItemViewSet)
router.register(r'payments', PaymentViewSet)
urlpatterns = router.urls

urlpatterns += [
    path("cart/add/", add_to_cart, name="add-to-cart"),
]
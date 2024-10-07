from django.urls import path
from rest_framework import routers
from .views import OrdersViewSet


router = routers.SimpleRouter()
# router.register(r'login', LoginView)
router.register(r'orders', OrdersViewSet)
urlpatterns = router.urls

urlpatterns += [
]
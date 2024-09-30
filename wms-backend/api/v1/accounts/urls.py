from django.urls import path
from rest_framework import routers
from .views import LoginView, StakeholderView


router = routers.SimpleRouter()
# router.register(r'login', LoginView)
# router.register(r'accounts', AccountViewSet)
urlpatterns = router.urls

urlpatterns += [
    path('login/', LoginView.as_view(), name='login'),
    path('stakeholders/', StakeholderView.as_view(), name='stakeholder_create'),
]
from django.urls import path
from rest_framework import routers
from .views import LoginView, StakeholderView, CustomPasswordResetView
from django.contrib.auth import views as auth_views


router = routers.SimpleRouter()
# router.register(r'login', LoginView)
router.register(r'stakeholders', StakeholderView)
urlpatterns = router.urls

urlpatterns += [
    path('login/', LoginView.as_view(), name='login'),
    
    path('password-reset/', CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
]
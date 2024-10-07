
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/accounts/', include('api.v1.accounts.urls')),
    path('api/inventory/', include('api.v1.inventory.urls')),
]

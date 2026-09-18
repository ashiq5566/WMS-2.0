
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/accounts/', include('api.v1.accounts.urls')),
    path('api/inventory/', include('api.v1.inventory.urls')),
    re_path(r'^(?!api|admin|static|media).*$', TemplateView.as_view(template_name="index.html"), name="app"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
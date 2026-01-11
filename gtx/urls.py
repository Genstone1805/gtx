from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('backend-admin/', admin.site.urls),
    path('admin/', include('control.urls')),
    path('account/', include('account.urls')),
    path('api/account/', include('account.urls')),
    path('cards/', include('cards.urls')),
] 
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

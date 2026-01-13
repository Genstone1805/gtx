from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    path('backend-admin/', admin.site.urls),
    path('admin/', include('control.urls')),
    path('account/', include('account.urls')),
    path('api/account/', include('account.urls')),
    path('cards/', include('cards.urls')),

    # DOcumentation Urls
    path('download-docs/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('schema/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
] 
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

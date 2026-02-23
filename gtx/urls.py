from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView


def backend_admin_entry(request):
    """
    Standalone entrypoint for Django admin:
    - anonymous users get admin login directly (no extra redirect hop)
    - authenticated staff/superusers get admin index directly
    """
    request.current_app = admin.site.name
    if admin.site.has_permission(request):
        return admin.site.index(request)
    return admin.site.login(request)


urlpatterns = [
    path('backend-admin', backend_admin_entry, name='backend-admin-entry-no-slash'),
    path('backend-admin/', backend_admin_entry, name='backend-admin-entry'),
    path('backend-admin/', admin.site.urls),
    path('admin/', include('control.urls')),
    path('api/admin/', include('control.urls')),
    path('account/', include('account.urls')),
    path('api/account/', include('account.urls')),
    path('cards/', include('cards.urls')),
    path('order/', include('order.urls')),
    path('withdrawal/', include('withdrawal.urls')),
    path('notifications/', include('notification.urls')),
    path('logs/', include('logs.urls')),

    # Frontend template URLs
    path('template/', include('frontend.urls')),

    # DOcumentation Urls
    path('download-docs/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('schema/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

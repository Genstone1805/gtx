"""
URLs for logs app.
"""
from django.urls import path
from .views import LogViewerView

app_name = 'logs'

urlpatterns = [
    path('', LogViewerView.as_view(), name='logs'),
]

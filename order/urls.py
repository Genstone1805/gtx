from django.urls import path
from .views import CreateGiftCardOrderView, CreateOrderPageView

urlpatterns = [
    path('create/', CreateGiftCardOrderView.as_view(), name='create_order'),
    path('create-page/', CreateOrderPageView.as_view(), name='create_order_page'),
]

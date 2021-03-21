from django.urls import path

from .views import (
    CourierCreateView, CourierUpdateView, OrderCreateView
)

urlpatterns = [
    path('couriers', CourierCreateView.as_view(), name='couriers__create'),
    path('couriers/<int:courier_id>', CourierUpdateView.as_view(), name='courier__update'),
    path('orders', OrderCreateView.as_view(), name='orders__create'),
]

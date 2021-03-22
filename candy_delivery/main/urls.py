from django.urls import path

from .views import (
    CouriersCreateView, CourierUpdateView, OrdersCreateView,
    OrdersAssignView,
)

urlpatterns = [
    path('couriers', CouriersCreateView.as_view(), name='couriers__create'),
    path('couriers/<int:courier_id>', CourierUpdateView.as_view(), name='courier__update'),
    path('orders', OrdersCreateView.as_view(), name='orders__create'),
    path('orders/assign', OrdersAssignView.as_view(), name='orders_assign'),
]

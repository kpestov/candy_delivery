from django.urls import path

from .views import (
    CouriersCreateView, OrdersCreateView,
    OrdersAssignView, OrdersCompleteView, CourierView
)

app_name = 'main'

urlpatterns = [
    path('couriers', CouriersCreateView.as_view(), name='couriers__create'),
    path('couriers/<int:courier_id>', CourierView.as_view(), name='courier'),
    path('orders', OrdersCreateView.as_view(), name='orders__create'),
    path('orders/assign', OrdersAssignView.as_view(), name='orders_assign'),
    path('orders/complete', OrdersCompleteView.as_view(), name='orders_complete'),
]

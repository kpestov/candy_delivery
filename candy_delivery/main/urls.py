from django.urls import path

from .views import CourierCreateView

urlpatterns = [
    path('couriers', CourierCreateView.as_view(), name='couriers__create'),
]

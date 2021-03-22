from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.views import APIView
from rest_framework.response import Response

from .serializers.courier import (
    CourierListSerializer, CourierListSerializerOut, CourierSerializer,
    UpdateCourierArgsSerializer, CourierSerializerOut, CourierSerializerIn
)
from .serializers.order import (
    OrderSerializer, OrderListSerializer,
    OrderListSerializerOut, OrdersAssignSerializer
)

from .models import Courier, Order
from .utils import CreateViewMixin


class CouriersCreateView(CreateViewMixin, APIView):
    obj_key = 'courier_id'
    objects_name = 'couriers'
    serializer = CourierSerializer
    serializer_list = CourierListSerializer
    serializer_out = CourierListSerializerOut


class OrdersCreateView(CreateViewMixin, APIView):
    obj_key = 'order_id'
    objects_name = 'orders'
    serializer = OrderSerializer
    serializer_list = OrderListSerializer
    serializer_out = OrderListSerializerOut


class CourierUpdateView(GenericAPIView):
    serializer_class = UpdateCourierArgsSerializer
    queryset = Courier

    def patch(self, request, courier_id):
        courier = get_object_or_404(self.queryset, pk=courier_id)
        updated_courier = self.get_serializer(courier, data=request.data).load_and_save()

        return Response(
                CourierSerializerOut(updated_courier).data,
                status=status.HTTP_200_OK
        )


class OrdersAssignView(GenericAPIView):
    serializer_class = OrdersAssignSerializer
    queryset = Order

    def post(self, request):
        orders = Order.objects.filter(id__in=[1, 2])

        validated_courier_data = CourierSerializerIn(data=request.data).load()
        courier_orders = Courier.get_suitable_orders(courier_id=validated_courier_data['courier_id'])

        assigned_orders = self.get_serializer(orders, data=request.data, partial=True).load_and_save()

        resp = {'orders': OrderListSerializerOut(assigned_orders, many=True).data}
        if orders:
            resp.update({'assign_time': orders[0].assign_time})

        return Response(resp, status=status.HTTP_200_OK)

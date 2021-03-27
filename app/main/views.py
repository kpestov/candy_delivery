from typing import Type

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.views import APIView
from rest_framework.response import Response

from . import base_serializers
from .serializers.courier import (
    CourierListSerializer, CourierListSerializerOut, CourierSerializer,
    UpdateCourierArgsSerializer, CourierSerializerOut, CourierSerializerIn
)
from .serializers.order import (
    OrderSerializer, OrderListSerializer,
    OrderListSerializerOut, OrdersAssignSerializer,
    OrderCompleteSerializer, OrderArgsSerializer
)
from .models import Courier, Order
from .utils import CreateViewMixin, get_object_or_400


class CouriersCreateView(CreateViewMixin, APIView):
    """View для загрузки курьеров в базу"""
    obj_key = 'courier_id'
    objects_name = 'couriers'
    serializer = CourierSerializer
    serializer_list = CourierListSerializer
    serializer_out = CourierListSerializerOut


class CourierView(GenericAPIView):
    """View для получения информации о курьере и доп. статистики, а также для обновления атрибутов курьера"""
    serializer_class = UpdateCourierArgsSerializer
    queryset = Courier

    def get(self, request, courier_id):
        courier = get_object_or_400(Courier, id=courier_id)
        courier_info = CourierSerializerOut(courier).data

        if courier.has_completed_orders:
            courier_info = {
                **courier_info, 'rating': courier.rating, 'earnings': courier.earnings
            }

        return Response(
            courier_info,
            status=status.HTTP_200_OK
        )

    def patch(self, request, courier_id):
        courier = get_object_or_404(self.queryset, pk=courier_id)
        updated_courier = self.get_serializer(courier, data=request.data).load_and_save()

        return Response(
                CourierSerializerOut(updated_courier).data,
                status=status.HTTP_200_OK
        )


class OrdersCreateView(CreateViewMixin, APIView):
    """View для создания заказов"""
    obj_key = 'order_id'
    objects_name = 'orders'
    serializer = OrderSerializer
    serializer_list = OrderListSerializer
    serializer_out = OrderListSerializerOut


class OrdersAssignView(GenericAPIView):
    """View для назначения курьеру максимального количества заказов, подходящих по весу, району и графику работы"""
    serializer_class = OrdersAssignSerializer
    queryset = Order

    def post(self, request):
        validated_courier_data = CourierSerializerIn(data=request.data).load()
        courier_orders = (
            Courier.objects
            .get(id=validated_courier_data['courier_id'])
            .get_suitable_orders(today=timezone.now())
        )

        assigned_orders = self.get_serializer(courier_orders, data=request.data, partial=True).load_and_save()

        resp = {'orders': OrderListSerializerOut(assigned_orders, many=True).data}
        if courier_orders:
            resp.update({'assign_time': courier_orders[-1].assign_time})

        return Response(resp, status=status.HTTP_200_OK)


class OrdersCompleteView(GenericAPIView):
    """View отмечает заказ выполненным"""
    serializer_class = OrderCompleteSerializer
    queryset = Order

    @staticmethod
    def get_and_validate_order(
            request,
            lookup_serializer: Type[base_serializers.Serializer] = OrderArgsSerializer
    ):
        lookup = lookup_serializer(data=request.data).load()

        return (
            Order.objects
            .filter(id=lookup.get('order_id'))
            .filter(courier_id=lookup.get('courier_id'))
            .filter(complete_time__isnull=True)
            .filter(assign_time__isnull=False)
        ).one_or_400()

    def post(self, request):
        instance = self.get_and_validate_order(request)
        completed_order = self.get_serializer(instance, data=request.data, partial=True).load_and_save()

        return Response(
            {'order_id': completed_order.pk},
            status=status.HTTP_200_OK
        )

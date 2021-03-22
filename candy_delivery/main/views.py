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
    OrderListSerializerOut
)

from .models import Courier
from .utils import CreateViewMixin, get_object_or_400


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


class OrdersAssignView(APIView):
    def post(self, request):
        courier_data = CourierSerializerIn(data=request.data).load()
        courier = get_object_or_400(Courier, id=courier_data.get('courier_id'))
        return Response({courier.pk})

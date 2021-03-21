from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.views import APIView
from rest_framework.response import Response

from .serializers.courier import (
    CourierListSerializer, CourierListSerializerOut, CourierSerializer,
    UpdateCourierArgsSerializer, CourierSerializerOut
)
from .exceptions import APIError
from .utils import collect_invalid_objects
from .models import Courier


class CourierCreateView(APIView):
    def post(self, request):
        invalid_couriers = collect_invalid_objects(request, CourierSerializer, obj_key='courier_id')
        if invalid_couriers:
            raise APIError(
                objects_name='couriers',
                invalid_objects=invalid_couriers
            )

        created_couriers = CourierListSerializer(data=request.data).load_and_save()
        return Response(
            {
                'couriers': CourierListSerializerOut(created_couriers, many=True).data
            },
            status=status.HTTP_201_CREATED
        )


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

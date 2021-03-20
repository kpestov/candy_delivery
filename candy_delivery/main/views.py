from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from .serializers import CourierListSerializer, CourierSerializerOut, CourierSerializer
from .exceptions import APIError


class CourierCreateView(APIView):
    def post(self, request):
        invalid_couriers = []
        for courier in request.data.get('data'):
            serializer = CourierSerializer(data=courier)
            if not serializer.is_valid():
                invalid_couriers.append({'id': serializer.data.get('courier_id')})

        if invalid_couriers:
            raise APIError(
                instances_name='couriers',
                invalid_instances=invalid_couriers
            )

        created_couriers = CourierListSerializer(data=request.data).load_and_save()
        return Response(
            {
                'couriers': CourierSerializerOut(created_couriers, many=True).data
            },
            status=status.HTTP_201_CREATED
        )

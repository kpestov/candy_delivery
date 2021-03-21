from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from .serializers import CourierListSerializer, CourierSerializerOut, CourierSerializer
from .exceptions import APIError
from .utils import collect_invalid_objects


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
                'couriers': CourierSerializerOut(created_couriers, many=True).data
            },
            status=status.HTTP_201_CREATED
        )

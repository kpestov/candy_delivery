from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from .serializers import CourierListSerializer, CourierSerializerOut


class CourierCreateView(APIView):
    def post(self, request):
        created_couriers = CourierListSerializer(data=request.data).load_and_save()
        return Response(
            {
                'couriers': CourierSerializerOut(created_couriers, many=True).data
            },
            status=status.HTTP_201_CREATED
        )

from datetime import datetime

from rest_framework.validators import ValidationError
from rest_framework.response import Response
from rest_framework import status

from .exceptions import APIError, Http400


def get_object_or_400(klass, *args, **kwargs):
    try:
        obj = klass.objects.get(*args, **kwargs)
    except klass.DoesNotExist:
        raise Http400()
    return obj


def collect_invalid_objects(request, serializer_cls, obj_key: str):
    invalid_objects = []
    for item in request.data.get('data'):
        serializer = serializer_cls(data=item)
        if not serializer.is_valid():
            invalid_objects.append({'id': serializer.data.get(obj_key)})
    return invalid_objects


def validate_time_intervals(time_intervals):
    valid_time_format = "%H:%M"
    for time_interval in time_intervals:
        try:
            start, end = time_interval.split('-')
            valid_start = datetime.strptime(start, valid_time_format)
            valid_end = datetime.strptime(end, valid_time_format)
            if valid_start > valid_end:
                raise ValidationError('Start time can not be greater than end time')
        except ValueError:
            raise ValidationError('Invalid input working hours')
    return time_intervals


class CreateViewMixin:
    obj_key = None
    objects_name = None
    serializer = None
    serializer_list = None
    serializer_out = None

    def post(self, request):
        invalid_objects = collect_invalid_objects(request, self.serializer, obj_key=self.obj_key)
        if invalid_objects:
            raise APIError(
                objects_name=self.objects_name,
                invalid_objects=invalid_objects
            )

        created_objects = self.serializer_list(data=request.data).load_and_save()
        return Response(
            {
                self.objects_name: self.serializer_out(created_objects, many=True).data
            },
            status=status.HTTP_201_CREATED
        )

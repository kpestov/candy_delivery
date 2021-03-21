from datetime import datetime

from rest_framework.validators import ValidationError


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

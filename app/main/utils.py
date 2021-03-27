from datetime import datetime
from typing import List

import django.urls
from django.utils.datastructures import MultiValueDict
from django.utils.http import urlencode

from rest_framework.validators import ValidationError
from rest_framework.response import Response
from rest_framework import status

from .exceptions import APIError, Http400


def get_object_or_400(klass, *args, **kwargs):
    try:
        obj = klass.objects.get(*args, **kwargs)
    except klass.DoesNotExist:
        raise Http400(details=f'{klass.__name__} does not exist')
    return obj


def collect_invalid_objects(request, serializer_cls, obj_key: str):
    """
    Утилита для сбора объектов, которые не прошли валидацию.
    Используется для отдачи в response body, когда кидается Http400
    """
    invalid_objects = []
    for item in request.data.get('data'):
        serializer = serializer_cls(data=item)
        if not serializer.is_valid():
            invalid_objects.append({'id': serializer.data.get(obj_key)})
    return invalid_objects


def validate_time_intervals(time_intervals: List[str]):
    """Валидация списка строковых временных интервалов, на соответствие формату: HH:MM-HH:MM"""
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


def cast_objects_to_hours(inst, attr_name):
    """Функция преобразует время из объектов типа OrderDeliveryHours или CourierWorkingHours в строку HH:MM-HH:MM"""
    time_format = '%H:%M'
    casted_hours = []
    for time_interval in getattr(inst, attr_name):
        start, end = time_interval.start, time_interval.end
        casted_hours.append(f'{start.strftime(time_format)}-{end.strftime(time_format)}')
    setattr(inst, attr_name, casted_hours)


def cast_hours_to_objects(
        inst,
        attr_name: str,
        to_obj,
        today: datetime
):
    """
    Функция преобразует время из строки в объекты типа OrderDeliveryHours или CourierWorkingHours.
    Благодаря данной функции удобно проводить пересечение дат у заказов и курьеров,
    и тем самым подбирать подходящие для курьеров заказы.
    """
    casted_hours = []
    time_format = '%H:%M'
    for time_interval in getattr(inst, attr_name):
        start, end = time_interval.split('-')
        start, end = datetime.strptime(start, time_format), datetime.strptime(end, time_format)
        casted_hours.append(
            to_obj(
                start=today.replace(
                    hour=start.hour, minute=start.minute, second=0, microsecond=0
                ),
                end=today.replace(
                    hour=end.hour, minute=end.minute, second=0, microsecond=0
                )
            )
        )
    setattr(inst, attr_name, sorted(casted_hours, key=lambda x: x.start))


def remove_time_intervals_over_current_time(inst, attr_time_interval: str, today):
    """Убирает временной промежуток, если время окончания (доставки зказа/работы курьера) < текущего времени"""
    valid_time_intervals = [
        time_interval for time_interval in getattr(inst, attr_time_interval)
        if time_interval.end.time() > today.time()
    ]
    setattr(inst, attr_time_interval, valid_time_intervals)


class CreateViewMixin:
    obj_key = None
    objects_name = None
    serializer = None
    serializer_list = None
    serializer_out = None

    def post(self, request):
        try:
            created_objects = self.serializer_list(data=request.data).load_and_save()
        except ValidationError as e:
            raise APIError(
                objects_name=self.objects_name,
                invalid_objects=collect_invalid_objects(request, self.serializer, obj_key=self.obj_key),
                details=e.get_full_details()
            )

        return Response(
            {
                self.objects_name: self.serializer_out(created_objects, many=True).data
            },
            status=status.HTTP_201_CREATED
        )


def reverse(view, urlconf=None, args=None, kwargs=None, current_app=None, query_kwargs=None):
    base_url = django.urls.reverse(view, urlconf=urlconf, args=args, kwargs=kwargs, current_app=current_app)

    if query_kwargs:
        return f'{base_url}?{urlencode(query_kwargs, doseq=isinstance(query_kwargs, MultiValueDict))}'

    return base_url

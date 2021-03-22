import logging

import rest_framework.views
from rest_framework import status
from rest_framework.exceptions import APIException


logger = logging.getLogger(__name__)


class APIError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Некорректный запрос'
    default_code = 'invalid'

    def __init__(self, objects_name=None, invalid_objects=None, detail=None, status_code=None, **kwargs):
        super().__init__(detail=detail, **kwargs)
        self.invalid_objects = invalid_objects
        self.objects_name = objects_name

        if status_code is not None:
            self.status_code = status_code

        if not isinstance(self.detail, str):
            raise ValueError('supported only str detail')


class Http400(APIError):
    pass


def exception_handler(exc, context):
    logger.exception(f'caught unhandled exception: {exc}')
    response = rest_framework.views.exception_handler(exc, context)

    if response is None:
        return response

    if isinstance(exc, APIError):
        response.data.pop('detail')
        response.data['validation_error'] = {exc.objects_name: exc.invalid_objects}

    if isinstance(exc, Http400):
        response.data.pop('validation_error')

    return response

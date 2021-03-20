import logging

import rest_framework.views
from rest_framework import status
from rest_framework.exceptions import APIException


logger = logging.getLogger(__name__)


class APIError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Некорректный запрос'
    default_code = 'invalid'

    def __init__(self, instances_name=None, invalid_instances=None, detail=None, status_code=None, **kwargs):
        super().__init__(detail=detail, **kwargs)
        self.invalid_instances = invalid_instances
        self.instances_name = instances_name

        if status_code is not None:
            self.status_code = status_code

        if not isinstance(self.detail, str):
            raise ValueError('supported only str detail')


def exception_handler(exc, context):
    logger.exception(f'caught unhandled exception: {exc}')
    response = rest_framework.views.exception_handler(exc, context)

    if response is None:
        return response

    if isinstance(exc, APIError):
        response.data.pop('detail')
        response.data['validation_error'] = {exc.instances_name: exc.invalid_instances}

    return response

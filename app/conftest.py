import pytest

from django.apps import apps

from rest_framework.test import APIClient

from app.main.utils import reverse


@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_createdb, django_db_blocker):
    if not django_db_createdb:
        return

    with django_db_blocker.unblock():
        models_to_delete = [
            *apps.get_app_config('main').get_models()
        ]

        for model in models_to_delete:
            if model._meta.managed:
                model._default_manager.all().delete()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def payload_to_create_couriers():
    return {
        "data": [
            {
                "courier_id": 1,
                "courier_type": "foot",
                "regions": [1, 12, 22],
                "working_hours": ["11:35-14:05", "09:00-18:00"]
            },
            {
                "courier_id": 2,
                "courier_type": "bike",
                "regions": [22],
                "working_hours": ["09:00-18:00"]
            },
            {
                "courier_id": 3,
                "courier_type": "car",
                "regions": [12, 22, 23, 33],
                "working_hours": []
            }
        ]
    }


@pytest.fixture
def payload_to_create_orders():
    return {
        "data": [
            {
                "order_id": 1,
                "weight": 0.23,
                "region": 12,
                "delivery_hours": ["09:00-18:00"]
            },
            {
                "order_id": 2,
                "weight": 15,
                "region": 1,
                "delivery_hours": ["09:00-18:00"]
            },
            {
                "order_id": 3,
                "weight": 0.01,
                "region": 22,
                "delivery_hours": ["09:00-12:00", "16:00-21:30"]
            }
        ]
    }


@pytest.fixture
def create_orders_and_couriers(api_client, payload_to_create_couriers, payload_to_create_orders):
    api_client.post(reverse('main:couriers__create'), payload_to_create_couriers)
    api_client.post(reverse('main:orders__create'), payload_to_create_orders)

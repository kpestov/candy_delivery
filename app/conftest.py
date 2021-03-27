import pytest

from django.apps import apps

from rest_framework.test import APIClient


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

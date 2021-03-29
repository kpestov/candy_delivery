import pytz
import pytest

from datetime import datetime
from unittest.mock import patch

from app.main.utils import reverse

CURRENT_DATE = datetime(2021, 3, 29, 11, 0, 0, tzinfo=pytz.utc)
COMPLETE_TIME = datetime(2021, 3, 29, 11, 30, 0, tzinfo=pytz.utc)

pytestmark = [pytest.mark.django_db]


def test_orders_create_successful(api_client, payload_to_create_orders):
    resp = api_client.post(reverse('main:orders__create'), payload_to_create_orders)
    assert resp.data == {'orders': [{'id': 1}, {'id': 2}, {'id': 3}]}
    assert resp.status_code == 201


@pytest.mark.parametrize('invalid_payload', argvalues=[
    ({"weight": 15, "region": 1, "delivery_hours": ["09:00-18:00"]}),
    ({"order_id": 1, "region": 1, "delivery_hours": ["09:00-18:00"]}),
    ({"order_id": 1, "weight": 15, "delivery_hours": ["09:00-18:00"]}),
    ({"order_id": 1, "weight": 15, "region": 1})
])
def test_orders_create_failed_without_required_attributes(invalid_payload, api_client):
    payload = {"data": [invalid_payload]}
    resp = api_client.post(reverse('main:orders__create'), payload)
    assert resp.status_code == 400


@pytest.mark.parametrize('invalid_payload', argvalues=[
    ({"order_id": 1, "weight": 0.001, "region": 1, "delivery_hours": ["09:00-18:00"]}),
    ({"order_id": 1, "weight": 90, "region": 1, "delivery_hours": ["09:00-18:00"]}),
    ({"order_id": 1, "weight": 51, "region": 1, "delivery_hours": ["09:00-18:00"]}),
    ({"order_id": 1, "weight": -1, "region": 1, "delivery_hours": ["09:00-18:00"]}),
])
def test_orders_create_failed_invalid_weight(invalid_payload, api_client):
    payload = {"data": [invalid_payload]}
    resp = api_client.post(reverse('main:orders__create'), payload)
    assert resp.status_code == 400


@pytest.mark.parametrize('invalid_payload', argvalues=[
    ({"order_id": 1, "weight": 1.0, "region": 1, "delivery_hours": ["0900-18:00"]}),
    ({"order_id": 1, "weight": 1.0, "region": 1, "delivery_hours": ["09:0018:00"]}),
    ({"order_id": 1, "weight": 1.0, "region": 1, "delivery_hours": ["09:-18:00"]}),
    ({"order_id": 1, "weight": 1.0, "region": 1, "delivery_hours": ["09-18:00"]}),
    ({"order_id": 1, "weight": 1.0, "region": 1, "delivery_hours": ["09:00"]}),
    ({"order_id": 1, "weight": 1.0, "region": 1, "delivery_hours": ["25:00-18:00"]}),
    ({"order_id": 1, "weight": 1.0, "region": 1, "delivery_hours": "09:00-18:00"}),
])
def test_orders_create_failed_invalid_working_hours_format(invalid_payload, api_client):
    payload = {"data": [invalid_payload]}
    resp = api_client.post(reverse('main:orders__create'), payload)
    assert resp.status_code == 400


def test_orders_create_failed_properly_collect_invalid_items(api_client):
    invalid_payload = {
        "data": [
            {
                "order_id": 1,
                "weight": 0.001,
                "region": 12,
                "delivery_hours": ["09:00-18:00"]
            },
            {
                "order_id": 2,
                "region": 1,
                "delivery_hours": ["09:00-18:00"]
            }
        ]
    }
    resp = api_client.post(reverse('main:orders__create'), invalid_payload)
    assert resp.data.get('validation_error') == {"orders": [{"id": 1}, {"id": 2}]}
    assert resp.status_code == 400


def test_orders_assign_not_found_suitable_orders(api_client, payload_to_create_couriers, payload_to_create_orders):
    payload_to_create_orders.update(
        {
            "data": [
                {
                    "order_id": 1,
                    "weight": 0.23,
                    "region": 7,
                    "delivery_hours": ["09:00-23:00"]
                }
            ]
        }
    )
    api_client.post(reverse('main:couriers__create'), payload_to_create_couriers)
    api_client.post(reverse('main:orders__create'), payload_to_create_orders)
    resp = api_client.post(reverse('main:orders_assign'), {'courier_id': 1})
    assert resp.status_code == 200
    assert resp.data == {"orders": []}


def test_orders_assign_not_found_courier(api_client, create_orders_and_couriers):
    resp = api_client.post(reverse('main:orders_assign'), {'courier_id': 8})
    assert resp.status_code == 400


@patch('app.main.views.OrdersAssignView.current_date', new=CURRENT_DATE)
def test_orders_assign_successful(api_client, create_orders_and_couriers):
    resp = api_client.post(reverse('main:orders_assign'), {'courier_id': 1})
    assert resp.status_code == 200
    assert resp.data == {"orders": [{"id": 1}, {"id": 3}], "assign_time": CURRENT_DATE}


@patch('app.main.views.OrdersAssignView.current_date', new=CURRENT_DATE)
def test_orders_complete_successful(api_client, create_orders_and_couriers):
    api_client.post(reverse('main:orders_assign'), {'courier_id': 1})
    complete_data = {"courier_id": 1, "order_id": 1, "complete_time": COMPLETE_TIME.strftime('%Y-%m-%dT%H:%M:%S')}
    resp = api_client.post(reverse('main:orders_complete'), complete_data)
    assert resp.status_code == 200
    assert resp.data == {"order_id": 1}


@patch('app.main.views.OrdersAssignView.current_date', new=CURRENT_DATE)
def test_orders_complete_failed_not_found_order(api_client, create_orders_and_couriers):
    api_client.post(reverse('main:orders_assign'), {'courier_id': 1})
    complete_data = {"courier_id": 1, "order_id": 4, "complete_time": COMPLETE_TIME.strftime('%Y-%m-%dT%H:%M:%S')}
    resp = api_client.post(reverse('main:orders_complete'), complete_data)
    assert resp.status_code == 400


@patch('app.main.views.OrdersAssignView.current_date', new=CURRENT_DATE)
def test_orders_complete_failed_assign_to_another_courier(api_client, create_orders_and_couriers):
    api_client.post(reverse('main:orders_assign'), {'courier_id': 1})
    complete_data = {"courier_id": 2, "order_id": 1, "complete_time": COMPLETE_TIME.strftime('%Y-%m-%dT%H:%M:%S')}
    resp = api_client.post(reverse('main:orders_complete'), complete_data)
    assert resp.status_code == 400


@patch('app.main.views.OrdersAssignView.current_date', new=CURRENT_DATE)
def test_orders_complete_failed_not_assigned_order(api_client, create_orders_and_couriers):
    complete_data = {"courier_id": 1, "order_id": 1, "complete_time": COMPLETE_TIME.strftime('%Y-%m-%dT%H:%M:%S')}
    resp = api_client.post(reverse('main:orders_complete'), complete_data)
    assert resp.status_code == 400

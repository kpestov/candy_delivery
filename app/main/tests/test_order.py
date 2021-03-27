import pytest

from app.main.utils import reverse

pytestmark = [pytest.mark.django_db]


def test_orders_create_successful(api_client):
    payload = {
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
    resp = api_client.post(reverse('main:orders__create'), payload)
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

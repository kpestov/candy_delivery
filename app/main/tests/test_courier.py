import pytest

from app.main.utils import reverse


pytestmark = [pytest.mark.django_db]


def test_couriers_create_successful(api_client):
    payload = {
        "data": [
            {
                "courier_id": 1,
                "courier_type": "foot",
                "regions": [1, 12, 22],
                "working_hours": ["11:35-14:05", "09:00-11:00"]
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
    resp = api_client.post(reverse('main:couriers__create'), payload)
    assert resp.data == {'couriers': [{'id': 1}, {'id': 2}, {'id': 3}]}
    assert resp.status_code == 201


@pytest.mark.parametrize('invalid_payload', argvalues=[
    ({"courier_type": "foot", "regions": [1, 12, 22], "working_hours": ["09:00-11:00"]}),
    ({"courier_id": 1, "regions": [1, 12, 22], "working_hours": ["0900-11:00"]}),
    ({"courier_id": 1, "courier_type": "foot", "working_hours": ["09:0011:00"]}),
    ({"courier_id": 1, "courier_type": "foot", "regions": [1, 12, 22]})
])
def test_couriers_create_failed_without_required_attributes(invalid_payload, api_client):
    payload = {"data": [invalid_payload]}
    resp = api_client.post(reverse('main:couriers__create'), payload)
    assert resp.status_code == 400


@pytest.mark.parametrize('invalid_payload', argvalues=[
    ({"courier_id": 1, "courier_type": "root", "regions": [1], "working_hours": ["09:00-11:00"]}),
    ({"courier_id": 1, "courier_type": 1, "regions": [1], "working_hours": ["09:00-11:00"]}),
    ({"courier_id": 1, "courier_type": '@!#$', "regions": [1], "working_hours": ["09:00-11:00"]}),
])
def test_couriers_create_failed_invalid_courier_type(invalid_payload, api_client):
    payload = {"data": [invalid_payload]}
    resp = api_client.post(reverse('main:couriers__create'), payload)
    assert resp.status_code == 400


@pytest.mark.parametrize('invalid_payload', argvalues=[
    ({"courier_id": 1, "courier_type": "foot", "regions": [1], "working_hours": ["0900-11:00"]}),
    ({"courier_id": 1, "courier_type": "foot", "regions": [1], "working_hours": ["09:0011:00"]}),
    ({"courier_id": 1, "courier_type": "foot", "regions": [1], "working_hours": ["09:00-11:"]}),
    ({"courier_id": 1, "courier_type": "foot", "regions": [1], "working_hours": ["09:00%11:00"]}),
])
def test_couriers_create_failed_invalid_working_hours_format(invalid_payload, api_client):
    payload = {"data": [invalid_payload]}
    resp = api_client.post(reverse('main:couriers__create'), payload)
    assert resp.status_code == 400


@pytest.mark.parametrize('invalid_payload', argvalues=[
    ({"courier_id": 1, "couriertype": "foot", "regions": [1], "working_hours": ["09:00-11:00"]}),
    ({"courier_id": 1, "courier_type": "foot", "region": [1], "working_hours": ["09:00-11:00"]}),
    ({"courier_id": 1, "courier_type": "foot", "regions": [1], "working": ["09:00-11:00"]}),
])
def test_couriers_create_failed_invalid_attrs_name(invalid_payload, api_client):
    payload = {"data": [invalid_payload]}
    resp = api_client.post(reverse('main:couriers__create'), payload)
    assert resp.data.get('validation_error') == {"couriers": [{"id": 1}]}
    assert resp.status_code == 400


def test_couriers_create_failed_properly_collect_invalid_items(api_client):
    invalid_payload = {
        "data": [
            {
                "courier_id": 1,
                "courier_type": "root",
                "regions": [1, 12, 22],
                "working_hours": ["11:35-14:05", "09:00-11:00"]
            },
            {
                "courier_id": 2,
                "courier_type": "bike",
                "regions": [22],
                "working_hours": ["09:0018:00"]
            },
        ]
    }
    resp = api_client.post(reverse('main:couriers__create'), invalid_payload)
    assert resp.data.get('validation_error') == {"couriers": [{"id": 1}, {"id": 2}]}
    assert resp.status_code == 400


# @pytest.mark.parametrize('invalid_payload', argvalues=[
#     ({"courier_id": 1, "courier_type": "root", "regions": [1, 12, 22], "working_hours": ["09:00-11:00"]}),
#     ({"courier_id": 1, "courier_type": "foot", "regions": [1, 12, 22], "working_hours": ["0900-11:00"]}),
#     ({"courier_id": 1, "courier_type": "foot", "regions": [1, 12, 22], "working_hours": ["09:0011:00"]}),
# ])

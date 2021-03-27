import pytest

from app.main.utils import reverse


@pytest.mark.django_db
def test_couriers_create(api_client):
    payload = {
        "data": [
            {
                "courier_id": 1,
                "courier_type": "foot",
                "regions": [1, 12, 22],
                "working_hours": ["11:35-14:05", "09:00-11:00"]
            }
        ]
    }
    resp = api_client.post(reverse('main:couriers__create'), payload)
    assert resp.status_code == 201

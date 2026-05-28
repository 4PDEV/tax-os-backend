from uuid import uuid4

import pytest

pytestmark = pytest.mark.integration


def _create_country(client, code: str = "RW", name: str = "Rwanda"):
    return client.post("/countries", json={"code": code, "name": name})


def test_create_country(client):
    response = _create_country(client)
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == "RW"
    assert data["name"] == "Rwanda"
    assert data["status"] == "active"
    assert "id" in data


def test_list_countries(client):
    _create_country(client, code="RW", name="Rwanda")
    _create_country(client, code="UG", name="Uganda")

    response = client.get("/countries")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert [item["name"] for item in data] == ["Rwanda", "Uganda"]


def test_get_country(client):
    created = _create_country(client).json()

    response = client.get(f"/countries/{created['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_update_country(client):
    created = _create_country(client).json()

    response = client.put(
        f"/countries/{created['id']}",
        json={"name": "Republic of Rwanda"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Republic of Rwanda"
    assert data["code"] == "RW"


def test_soft_delete_country(client):
    created = _create_country(client).json()

    response = client.delete(f"/countries/{created['id']}")
    assert response.status_code == 200
    assert response.json()["status"] == "inactive"

    listed = client.get("/countries")
    assert listed.status_code == 200
    assert listed.json()[0]["status"] == "inactive"


def test_country_create_missing_required_field(client):
    response = client.post("/countries", json={"code": "RW"})
    assert response.status_code == 422


def test_country_create_duplicate_code_returns_conflict(client):
    first = _create_country(client, code="RW", name="Rwanda")
    assert first.status_code == 200

    duplicate = _create_country(client, code="RW", name="Other Rwanda")
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"] == "Country code already exists"


def test_country_get_invalid_id_returns_not_found(client):
    response = client.get(f"/countries/{uuid4()}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Country not found"


def test_country_create_malformed_payload(client):
    response = client.post("/countries", json={"code": 123, "name": "Rwanda"})
    assert response.status_code == 422

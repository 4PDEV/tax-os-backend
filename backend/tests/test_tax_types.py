from uuid import uuid4

import pytest

pytestmark = pytest.mark.integration


def _create_country(client):
    response = client.post("/countries", json={"code": "RW", "name": "Rwanda"})
    assert response.status_code == 200
    return response.json()


def _create_tax_type(client, country_id: str):
    payload = {
        "country_id": country_id,
        "code": "VAT",
        "name": "Value Added Tax",
        "description": "Indirect tax",
    }
    return client.post("/tax-types", json=payload)


def test_create_tax_type(client):
    country = _create_country(client)

    response = _create_tax_type(client, country["id"])
    assert response.status_code == 200
    data = response.json()
    assert data["country_id"] == country["id"]
    assert data["code"] == "VAT"
    assert data["status"] == "active"


def test_list_tax_types(client):
    country = _create_country(client)
    _create_tax_type(client, country["id"])
    client.post(
        "/tax-types",
        json={
            "country_id": country["id"],
            "code": "PAYE",
            "name": "Pay As You Earn",
            "description": None,
        },
    )

    response = client.get("/tax-types")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert [item["name"] for item in data] == ["Pay As You Earn", "Value Added Tax"]


def test_get_tax_type(client):
    country = _create_country(client)
    created = _create_tax_type(client, country["id"]).json()

    response = client.get(f"/tax-types/{created['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_update_tax_type(client):
    country = _create_country(client)
    created = _create_tax_type(client, country["id"]).json()

    response = client.put(
        f"/tax-types/{created['id']}",
        json={"name": "VAT Updated"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "VAT Updated"


def test_soft_delete_tax_type(client):
    country = _create_country(client)
    created = _create_tax_type(client, country["id"]).json()

    response = client.delete(f"/tax-types/{created['id']}")
    assert response.status_code == 200
    assert response.json()["status"] == "inactive"


def test_tax_type_create_invalid_foreign_key(client):
    response = client.post(
        "/tax-types",
        json={
            "country_id": str(uuid4()),
            "code": "VAT",
            "name": "Value Added Tax",
        },
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Country not found"


def test_tax_type_create_missing_required_field(client):
    country = _create_country(client)
    response = client.post(
        "/tax-types",
        json={"country_id": country["id"], "name": "Value Added Tax"},
    )
    assert response.status_code == 422


def test_tax_type_get_invalid_id_returns_not_found(client):
    response = client.get(f"/tax-types/{uuid4()}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Tax type not found"


def test_tax_type_create_malformed_payload(client):
    response = client.post(
        "/tax-types",
        json={
            "country_id": "not-a-uuid",
            "code": "VAT",
            "name": "Value Added Tax",
        },
    )
    assert response.status_code == 422

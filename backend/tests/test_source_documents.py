from uuid import uuid4

import pytest

pytestmark = pytest.mark.integration


def _create_country(client):
    response = client.post("/countries", json={"code": "RW", "name": "Rwanda"})
    assert response.status_code == 200
    return response.json()


def _create_tax_type(client, country_id: str):
    response = client.post(
        "/tax-types",
        json={
            "country_id": country_id,
            "code": "VAT",
            "name": "Value Added Tax",
        },
    )
    assert response.status_code == 200
    return response.json()


def _create_source_document(client, country_id: str, tax_type_id: str | None = None):
    payload = {
        "country_id": country_id,
        "tax_type_id": tax_type_id,
        "source_type": "law",
        "authority_level": "national",
        "title": "VAT Law",
        "short_title": "VAT",
        "issuing_authority": "Parliament",
        "official_reference": "Law 001/2026",
        "source_url": "https://example.org/vat-law",
        "language": "en",
    }
    return client.post("/source-documents", json=payload)


def test_create_source_document(client):
    country = _create_country(client)
    tax_type = _create_tax_type(client, country["id"])

    response = _create_source_document(client, country["id"], tax_type["id"])
    assert response.status_code == 200
    data = response.json()
    assert data["country_id"] == country["id"]
    assert data["tax_type_id"] == tax_type["id"]
    assert data["title"] == "VAT Law"
    assert data["status"] == "active"


def test_list_source_documents(client):
    country = _create_country(client)
    _create_source_document(client, country["id"])
    client.post(
        "/source-documents",
        json={
            "country_id": country["id"],
            "source_type": "guidance",
            "authority_level": "administrative",
            "title": "Admin Circular",
        },
    )

    response = client.get("/source-documents")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert [item["title"] for item in data] == ["Admin Circular", "VAT Law"]


def test_get_source_document(client):
    country = _create_country(client)
    created = _create_source_document(client, country["id"]).json()

    response = client.get(f"/source-documents/{created['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_update_source_document(client):
    country = _create_country(client)
    created = _create_source_document(client, country["id"]).json()

    response = client.put(
        f"/source-documents/{created['id']}",
        json={"title": "VAT Law Updated"},
    )
    assert response.status_code == 200
    assert response.json()["title"] == "VAT Law Updated"


def test_soft_delete_source_document(client):
    country = _create_country(client)
    created = _create_source_document(client, country["id"]).json()

    response = client.delete(f"/source-documents/{created['id']}")
    assert response.status_code == 200
    assert response.json()["status"] == "inactive"


def test_source_document_create_missing_required_field(client):
    country = _create_country(client)
    response = client.post(
        "/source-documents",
        json={"country_id": country["id"], "title": "VAT Law"},
    )
    assert response.status_code == 422


def test_source_document_create_invalid_country(client):
    response = client.post(
        "/source-documents",
        json={
            "country_id": str(uuid4()),
            "source_type": "law",
            "authority_level": "national",
            "title": "VAT Law",
        },
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Country not found"


def test_source_document_create_invalid_tax_type(client):
    country = _create_country(client)
    response = client.post(
        "/source-documents",
        json={
            "country_id": country["id"],
            "tax_type_id": str(uuid4()),
            "source_type": "law",
            "authority_level": "national",
            "title": "VAT Law",
        },
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Tax type not found"


def test_source_document_get_invalid_id_returns_not_found(client):
    response = client.get(f"/source-documents/{uuid4()}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Source document not found"

from uuid import uuid4

import pytest

pytestmark = pytest.mark.integration


def _create_country(client):
    response = client.post("/countries", json={"code": "RW", "name": "Rwanda"})
    assert response.status_code == 200
    return response.json()


def _create_source_document(client, country_id: str):
    response = client.post(
        "/source-documents",
        json={
            "country_id": country_id,
            "source_type": "law",
            "authority_level": "national",
            "title": "VAT Law",
        },
    )
    assert response.status_code == 200
    return response.json()


def _create_source_version(client, source_document_id: str, supersedes_version_id: str | None = None):
    payload = {
        "source_document_id": source_document_id,
        "version_label": "v1",
        "publication_date": "2026-01-01",
        "effective_from": "2026-01-01",
        "checksum_sha256": "a" * 64,
        "storage_path": "/registry/rw/vat/v1.pdf",
        "mime_type": "application/pdf",
        "file_size": 1024,
        "version_status": "active",
        "supersedes_version_id": supersedes_version_id,
        "notes": "Initial publication",
    }
    return client.post("/source-versions", json=payload)


def test_create_source_version(client):
    country = _create_country(client)
    document = _create_source_document(client, country["id"])

    response = _create_source_version(client, document["id"])
    assert response.status_code == 200
    data = response.json()
    assert data["source_document_id"] == document["id"]
    assert data["version_label"] == "v1"
    assert data["checksum_sha256"] == "a" * 64


def test_list_source_versions(client):
    country = _create_country(client)
    document = _create_source_document(client, country["id"])
    _create_source_version(client, document["id"])
    client.post(
        "/source-versions",
        json={
            "source_document_id": document["id"],
            "version_label": "v2",
            "checksum_sha256": "b" * 64,
            "storage_path": "/registry/rw/vat/v2.pdf",
        },
    )

    response = client.get("/source-versions")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert {item["version_label"] for item in data} == {"v1", "v2"}


def test_get_source_version(client):
    country = _create_country(client)
    document = _create_source_document(client, country["id"])
    created = _create_source_version(client, document["id"]).json()

    response = client.get(f"/source-versions/{created['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_source_version_create_missing_required_field(client):
    country = _create_country(client)
    document = _create_source_document(client, country["id"])
    response = client.post(
        "/source-versions",
        json={
            "source_document_id": document["id"],
            "checksum_sha256": "a" * 64,
        },
    )
    assert response.status_code == 422


def test_source_version_create_invalid_source_document(client):
    response = client.post(
        "/source-versions",
        json={
            "source_document_id": str(uuid4()),
            "version_label": "v1",
            "checksum_sha256": "a" * 64,
            "storage_path": "/registry/rw/vat/v1.pdf",
        },
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Source document not found"


def test_source_version_create_invalid_superseded_version(client):
    country = _create_country(client)
    document = _create_source_document(client, country["id"])
    response = _create_source_version(client, document["id"], supersedes_version_id=str(uuid4()))
    assert response.status_code == 404
    assert response.json()["detail"] == "Superseded source version not found"


def test_source_versions_are_immutable_update_not_allowed(client):
    country = _create_country(client)
    document = _create_source_document(client, country["id"])
    created = _create_source_version(client, document["id"]).json()

    response = client.put(f"/source-versions/{created['id']}", json={"version_label": "v1.1"})
    assert response.status_code == 405


def test_source_versions_are_immutable_delete_not_allowed(client):
    country = _create_country(client)
    document = _create_source_document(client, country["id"])
    created = _create_source_version(client, document["id"]).json()

    response = client.delete(f"/source-versions/{created['id']}")
    assert response.status_code == 405


def test_source_version_superseding_workflow_is_supported(client):
    country = _create_country(client)
    document = _create_source_document(client, country["id"])
    first = _create_source_version(client, document["id"]).json()

    response = client.post(
        "/source-versions",
        json={
            "source_document_id": document["id"],
            "version_label": "v2",
            "checksum_sha256": "b" * 64,
            "storage_path": "/registry/rw/vat/v2.pdf",
            "supersedes_version_id": first["id"],
        },
    )
    assert response.status_code == 200
    assert response.json()["supersedes_version_id"] == first["id"]

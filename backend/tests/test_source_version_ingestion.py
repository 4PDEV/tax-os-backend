from uuid import uuid4

import pytest

from app.storage.checksum import sha256_bytes

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


def _create_source_version(client, source_document_id: str, **extra):
    content = extra.pop("content", b"ingestion workflow content")
    checksum = sha256_bytes(content)
    payload = {
        "source_document_id": source_document_id,
        "version_label": "v1",
        "checksum_sha256": checksum,
        "storage_path": extra.pop("storage_path", "rw/vat/v1/ingestion.pdf"),
        **extra,
    }
    response = client.post("/source-versions", json=payload)
    assert response.status_code == 200
    return response.json(), content


def test_create_source_version_defaults_to_not_started(client):
    country = _create_country(client)
    document = _create_source_document(client, country["id"])
    version, _ = _create_source_version(client, document["id"])

    assert version["ingestion_status"] == "not_started"


def test_upload_transitions_ingestion_status_to_queued(client):
    country = _create_country(client)
    document = _create_source_document(client, country["id"])
    version, content = _create_source_version(client, document["id"])

    response = client.post(
        f"/source-versions/{version['id']}/upload",
        files={"file": ("ingestion.pdf", content, "application/pdf")},
    )
    assert response.status_code == 200
    assert response.json()["ingestion_status"] == "queued"


def test_ingestion_status_transition_processing_to_parsed(client):
    country = _create_country(client)
    document = _create_source_document(client, country["id"])
    version, content = _create_source_version(client, document["id"])
    client.post(
        f"/source-versions/{version['id']}/upload",
        files={"file": ("ingestion.pdf", content, "application/pdf")},
    )

    queued = client.post(
        f"/source-versions/{version['id']}/ingestion-status",
        json={"ingestion_status": "processing"},
    )
    assert queued.status_code == 200
    assert queued.json()["ingestion_status"] == "processing"

    parsed = client.post(
        f"/source-versions/{version['id']}/ingestion-status",
        json={"ingestion_status": "parsed"},
    )
    assert parsed.status_code == 200
    assert parsed.json()["ingestion_status"] == "parsed"


def test_ingestion_status_rejects_invalid_transition(client):
    country = _create_country(client)
    document = _create_source_document(client, country["id"])
    version, _ = _create_source_version(client, document["id"])

    response = client.post(
        f"/source-versions/{version['id']}/ingestion-status",
        json={"ingestion_status": "parsed"},
    )
    assert response.status_code == 422
    assert "not allowed" in response.json()["detail"].lower()


def test_superseding_marks_prior_version_as_superseded(client):
    country = _create_country(client)
    document = _create_source_document(client, country["id"])
    first, content = _create_source_version(
        client,
        document["id"],
        storage_path="rw/vat/v1/first.pdf",
    )
    client.post(
        f"/source-versions/{first['id']}/upload",
        files={"file": ("first.pdf", content, "application/pdf")},
    )

    second = client.post(
        "/source-versions",
        json={
            "source_document_id": document["id"],
            "version_label": "v2",
            "checksum_sha256": sha256_bytes(b"second version"),
            "storage_path": "rw/vat/v1/second.pdf",
            "supersedes_version_id": first["id"],
        },
    )
    assert second.status_code == 200

    prior = client.get(f"/source-versions/{first['id']}")
    assert prior.status_code == 200
    assert prior.json()["ingestion_status"] == "superseded"


def test_ingestion_status_version_not_found(client):
    response = client.post(
        f"/source-versions/{uuid4()}/ingestion-status",
        json={"ingestion_status": "queued"},
    )
    assert response.status_code == 404

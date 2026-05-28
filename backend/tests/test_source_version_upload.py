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


def _create_source_version(client, source_document_id: str, *, content: bytes, storage_path: str):
    checksum = sha256_bytes(content)
    response = client.post(
        "/source-versions",
        json={
            "source_document_id": source_document_id,
            "version_label": "v1",
            "checksum_sha256": checksum,
            "storage_path": storage_path,
        },
    )
    assert response.status_code == 200
    return response.json()


def test_upload_source_version_file(client):
    country = _create_country(client)
    document = _create_source_document(client, country["id"])
    content = b"raw statute content for deterministic storage"
    version = _create_source_version(
        client,
        document["id"],
        content=content,
        storage_path="rw/vat/v1/statute.pdf",
    )

    response = client.post(
        f"/source-versions/{version['id']}/upload",
        files={"file": ("statute.pdf", content, "application/pdf")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["storage_path"] == "rw/vat/v1/statute.pdf"
    assert data["checksum_sha256"] == sha256_bytes(content)
    assert data["file_size"] == len(content)
    assert data["mime_type"] == "application/pdf"
    assert data["file_attached"] is True
    assert data["attachment_status"] == "attached"


def test_get_source_version_before_upload_is_pending(client):
    country = _create_country(client)
    document = _create_source_document(client, country["id"])
    content = b"pending attachment"
    version = _create_source_version(
        client,
        document["id"],
        content=content,
        storage_path="rw/vat/v1/pending.pdf",
    )

    response = client.get(f"/source-versions/{version['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["file_attached"] is False
    assert data["attachment_status"] == "pending"


def test_upload_rejects_inconsistent_partial_metadata(client):
    country = _create_country(client)
    document = _create_source_document(client, country["id"])
    content = b"partial metadata case"
    checksum = sha256_bytes(content)
    version = client.post(
        "/source-versions",
        json={
            "source_document_id": document["id"],
            "version_label": "v1",
            "checksum_sha256": checksum,
            "storage_path": "rw/vat/v1/partial.pdf",
            "file_size": len(content),
        },
    ).json()

    response = client.post(
        f"/source-versions/{version['id']}/upload",
        files={"file": ("partial.pdf", content, "application/pdf")},
    )
    assert response.status_code == 422
    assert "inconsistent" in response.json()["detail"].lower()


def test_upload_without_explicit_content_type_persists_mime_type(client):
    country = _create_country(client)
    document = _create_source_document(client, country["id"])
    content = b"upload without explicit multipart content type"
    version = _create_source_version(
        client,
        document["id"],
        content=content,
        storage_path="rw/vat/v1/no-explicit-mime.pdf",
    )

    response = client.post(
        f"/source-versions/{version['id']}/upload",
        files={"file": ("no-explicit-mime.pdf", content)},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["mime_type"]
    assert data["file_attached"] is True
    assert data["attachment_status"] == "attached"


def test_upload_rejects_checksum_mismatch(client):
    country = _create_country(client)
    document = _create_source_document(client, country["id"])
    version = _create_source_version(
        client,
        document["id"],
        content=b"expected-content",
        storage_path="rw/vat/v1/statute.pdf",
    )

    response = client.post(
        f"/source-versions/{version['id']}/upload",
        files={"file": ("statute.pdf", b"different-content", "application/pdf")},
    )
    assert response.status_code == 422
    assert "checksum" in response.json()["detail"].lower()


def test_upload_rejects_duplicate_upload(client):
    country = _create_country(client)
    document = _create_source_document(client, country["id"])
    content = b"immutable upload content"
    version = _create_source_version(
        client,
        document["id"],
        content=content,
        storage_path="rw/vat/v1/statute.pdf",
    )

    first = client.post(
        f"/source-versions/{version['id']}/upload",
        files={"file": ("statute.pdf", content, "application/pdf")},
    )
    assert first.status_code == 200

    second = client.post(
        f"/source-versions/{version['id']}/upload",
        files={"file": ("statute.pdf", content, "application/pdf")},
    )
    assert second.status_code == 409
    assert "already attached" in second.json()["detail"].lower()


def test_upload_rejects_empty_file(client):
    country = _create_country(client)
    document = _create_source_document(client, country["id"])
    version = _create_source_version(
        client,
        document["id"],
        content=b"placeholder",
        storage_path="rw/vat/v1/empty.pdf",
    )

    response = client.post(
        f"/source-versions/{version['id']}/upload",
        files={"file": ("empty.pdf", b"", "application/pdf")},
    )
    assert response.status_code == 422


def test_upload_version_not_found(client):
    response = client.post(
        f"/source-versions/{uuid4()}/upload",
        files={"file": ("missing.pdf", b"content", "application/pdf")},
    )
    assert response.status_code == 404


def test_upload_put_still_not_allowed_after_upload(client):
    country = _create_country(client)
    document = _create_source_document(client, country["id"])
    content = b"governance content"
    version = _create_source_version(
        client,
        document["id"],
        content=content,
        storage_path="rw/vat/v1/statute.pdf",
    )
    upload = client.post(
        f"/source-versions/{version['id']}/upload",
        files={"file": ("statute.pdf", content, "application/pdf")},
    )
    assert upload.status_code == 200

    response = client.put(
        f"/source-versions/{version['id']}",
        json={"version_label": "v1.1"},
    )
    assert response.status_code == 405

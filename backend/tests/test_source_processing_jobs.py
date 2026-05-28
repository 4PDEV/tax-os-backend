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


def _create_and_upload_version(client, document_id: str, content: bytes, storage_path: str):
    checksum = sha256_bytes(content)
    version = client.post(
        "/source-versions",
        json={
            "source_document_id": document_id,
            "version_label": "v1",
            "checksum_sha256": checksum,
            "storage_path": storage_path,
        },
    ).json()
    upload = client.post(
        f"/source-versions/{version['id']}/upload",
        files={"file": ("source.pdf", content, "application/pdf")},
    )
    assert upload.status_code == 200
    assert upload.json()["ingestion_status"] == "queued"
    return version


def test_enqueue_processing_job(client):
    country = _create_country(client)
    document = _create_source_document(client, country["id"])
    content = b"queue job content"
    version = _create_and_upload_version(client, document["id"], content, "rw/vat/v1/queue.pdf")

    response = client.post(
        "/source-processing-jobs",
        json={"source_version_id": version["id"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["source_version_id"] == version["id"]
    assert data["job_type"] == "source_ingestion"
    assert data["job_status"] == "queued"
    assert data["attempt_count"] == 0


def test_enqueue_rejects_duplicate_active_job(client):
    country = _create_country(client)
    document = _create_source_document(client, country["id"])
    content = b"duplicate queue test"
    version = _create_and_upload_version(client, document["id"], content, "rw/vat/v1/dup.pdf")

    first = client.post("/source-processing-jobs", json={"source_version_id": version["id"]})
    assert first.status_code == 200

    second = client.post("/source-processing-jobs", json={"source_version_id": version["id"]})
    assert second.status_code == 409


def test_enqueue_rejects_when_ingestion_not_queued(client):
    country = _create_country(client)
    document = _create_source_document(client, country["id"])
    version = client.post(
        "/source-versions",
        json={
            "source_document_id": document["id"],
            "version_label": "v1",
            "checksum_sha256": sha256_bytes(b"not uploaded"),
            "storage_path": "rw/vat/v1/pending.pdf",
        },
    ).json()

    response = client.post(
        "/source-processing-jobs",
        json={"source_version_id": version["id"]},
    )
    assert response.status_code == 422
    assert "queued" in response.json()["detail"].lower()


def test_job_status_transition_processing_to_completed(client):
    country = _create_country(client)
    document = _create_source_document(client, country["id"])
    content = b"status transition content"
    version = _create_and_upload_version(client, document["id"], content, "rw/vat/v1/status.pdf")

    job = client.post(
        "/source-processing-jobs",
        json={"source_version_id": version["id"]},
    ).json()

    processing = client.post(
        f"/source-processing-jobs/{job['id']}/status",
        json={"job_status": "processing"},
    )
    assert processing.status_code == 200
    assert processing.json()["attempt_count"] == 1

    completed = client.post(
        f"/source-processing-jobs/{job['id']}/status",
        json={"job_status": "completed"},
    )
    assert completed.status_code == 200
    assert completed.json()["job_status"] == "completed"
    assert completed.json()["completed_at"] is not None


def test_job_failure_requires_last_error(client):
    country = _create_country(client)
    document = _create_source_document(client, country["id"])
    content = b"failure content"
    version = _create_and_upload_version(client, document["id"], content, "rw/vat/v1/fail.pdf")

    job = client.post(
        "/source-processing-jobs",
        json={"source_version_id": version["id"]},
    ).json()
    client.post(f"/source-processing-jobs/{job['id']}/status", json={"job_status": "processing"})

    response = client.post(
        f"/source-processing-jobs/{job['id']}/status",
        json={"job_status": "failed"},
    )
    assert response.status_code == 422

    failed = client.post(
        f"/source-processing-jobs/{job['id']}/status",
        json={"job_status": "failed", "last_error": "parser unavailable"},
    )
    assert failed.status_code == 200
    assert failed.json()["last_error"] == "parser unavailable"


def test_list_processing_jobs_by_status(client):
    country = _create_country(client)
    document = _create_source_document(client, country["id"])
    content = b"list filter content"
    version = _create_and_upload_version(client, document["id"], content, "rw/vat/v1/list.pdf")
    client.post("/source-processing-jobs", json={"source_version_id": version["id"]})

    response = client.get("/source-processing-jobs", params={"job_status": "queued"})
    assert response.status_code == 200
    assert len(response.json()) >= 1
    assert all(item["job_status"] == "queued" for item in response.json())


def test_get_processing_job_not_found(client):
    response = client.get(f"/source-processing-jobs/{uuid4()}")
    assert response.status_code == 404

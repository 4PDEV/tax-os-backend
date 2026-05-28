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
    return version


def _enqueue_job(client, version_id: str):
    response = client.post(
        "/source-processing-jobs",
        json={"source_version_id": version_id},
    )
    assert response.status_code == 200
    return response.json()


def test_claim_next_processing_job(client):
    country = _create_country(client)
    document = _create_source_document(client, country["id"])
    content = b"claim next job content"
    version = _create_and_upload_version(client, document["id"], content, "rw/vat/v1/claim.pdf")
    job = _enqueue_job(client, version["id"])

    response = client.post(
        "/source-processing-jobs/claim-next",
        json={"locked_by": "worker-alpha"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == job["id"]
    assert data["job_status"] == "processing"
    assert data["attempt_count"] == 1
    assert data["locked_by"] == "worker-alpha"
    assert data["locked_at"] is not None
    assert data["started_at"] is not None

    version = client.get(f"/source-versions/{job['source_version_id']}")
    assert version.status_code == 200
    assert version.json()["ingestion_status"] == "processing"


def test_claim_next_returns_404_when_no_queued_jobs(client):
    response = client.post(
        "/source-processing-jobs/claim-next",
        json={"locked_by": "worker-alpha"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "no queued processing job available"


def test_claim_next_prevents_double_claim_of_same_job(client):
    country = _create_country(client)
    document = _create_source_document(client, country["id"])
    content = b"double claim prevention"
    version = _create_and_upload_version(client, document["id"], content, "rw/vat/v1/double.pdf")
    _enqueue_job(client, version["id"])

    first = client.post(
        "/source-processing-jobs/claim-next",
        json={"locked_by": "worker-one"},
    )
    assert first.status_code == 200

    second = client.post(
        "/source-processing-jobs/claim-next",
        json={"locked_by": "worker-two"},
    )
    assert second.status_code == 404


def test_claim_next_selects_highest_priority_job(client):
    country = _create_country(client)
    document = _create_source_document(client, country["id"])

    low = _create_and_upload_version(client, document["id"], b"low", "rw/vat/v1/low.pdf")
    high = _create_and_upload_version(client, document["id"], b"high", "rw/vat/v1/high.pdf")

    low_job = client.post(
        "/source-processing-jobs",
        json={"source_version_id": low["id"], "priority": 1},
    ).json()
    high_job = client.post(
        "/source-processing-jobs",
        json={"source_version_id": high["id"], "priority": 10},
    ).json()

    response = client.post(
        "/source-processing-jobs/claim-next",
        json={"locked_by": "worker-priority"},
    )
    assert response.status_code == 200
    assert response.json()["id"] == high_job["id"]
    assert response.json()["id"] != low_job["id"]

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


def _enqueue_and_claim(client, version_id: str):
    job = client.post(
        "/source-processing-jobs",
        json={"source_version_id": version_id},
    ).json()
    claimed = client.post(
        "/source-processing-jobs/claim-next",
        json={"locked_by": "worker-finalize"},
    )
    assert claimed.status_code == 200
    assert claimed.json()["id"] == job["id"]
    return job, claimed.json()


def test_complete_processing_job_with_result_json(client):
    country = _create_country(client)
    document = _create_source_document(client, country["id"])
    content = b"finalize complete content"
    version = _create_and_upload_version(client, document["id"], content, "rw/vat/v1/complete.pdf")
    job, claimed = _enqueue_and_claim(client, version["id"])

    response = client.post(
        f"/source-processing-jobs/{job['id']}/complete",
        json={
            "completed_by": "worker-finalize",
            "result_json": {"pages": 10, "language": "en"},
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["job_status"] == "completed"
    assert data["completed_by"] == "worker-finalize"
    assert data["result_json"] == {"pages": 10, "language": "en"}
    assert data["failed_by"] is None

    version_state = client.get(f"/source-versions/{version['id']}")
    assert version_state.json()["ingestion_status"] == "parsed"


def test_fail_processing_job_with_result_metadata(client):
    country = _create_country(client)
    document = _create_source_document(client, country["id"])
    content = b"finalize failure content"
    version = _create_and_upload_version(client, document["id"], content, "rw/vat/v1/fail.pdf")
    job, _ = _enqueue_and_claim(client, version["id"])

    response = client.post(
        f"/source-processing-jobs/{job['id']}/fail",
        json={
            "failed_by": "worker-finalize",
            "last_error": "deterministic parser failure",
            "result_json": {"stage": "parse"},
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["job_status"] == "failed"
    assert data["failed_by"] == "worker-finalize"
    assert data["last_error"] == "deterministic parser failure"
    assert data["result_json"] == {"stage": "parse"}

    version_state = client.get(f"/source-versions/{version['id']}")
    assert version_state.json()["ingestion_status"] == "failed"


def test_complete_rejects_job_not_in_processing(client):
    country = _create_country(client)
    document = _create_source_document(client, country["id"])
    content = b"not processing"
    version = _create_and_upload_version(client, document["id"], content, "rw/vat/v1/not-processing.pdf")
    job = client.post(
        "/source-processing-jobs",
        json={"source_version_id": version["id"]},
    ).json()

    response = client.post(
        f"/source-processing-jobs/{job['id']}/complete",
        json={"completed_by": "worker-finalize", "result_json": {}},
    )
    assert response.status_code == 422
    assert "processing" in response.json()["detail"].lower()


def test_complete_rejects_repeat_finalization(client):
    country = _create_country(client)
    document = _create_source_document(client, country["id"])
    content = b"repeat finalize"
    version = _create_and_upload_version(client, document["id"], content, "rw/vat/v1/repeat.pdf")
    job, _ = _enqueue_and_claim(client, version["id"])

    first = client.post(
        f"/source-processing-jobs/{job['id']}/complete",
        json={"completed_by": "worker-finalize", "result_json": {"ok": True}},
    )
    assert first.status_code == 200

    second = client.post(
        f"/source-processing-jobs/{job['id']}/complete",
        json={"completed_by": "worker-finalize", "result_json": {"ok": True}},
    )
    assert second.status_code == 422

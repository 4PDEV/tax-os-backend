from pathlib import Path

import pytest

from app.models.source_version import SourceVersion
from app.services.fetch import (
    DryRunFetcher,
    FetchRequest,
    LocalFixtureFetcher,
    detect_content_type,
    execute_fetch,
    sha256_bytes,
)
from app.services.fetch.safety import FetchSafetyError


def _fixture_root() -> Path:
    return Path(__file__).resolve().parent / "fixtures" / "fetch"


def test_dry_run_fetcher_success():
    fetcher = DryRunFetcher()
    request = FetchRequest(
        requested_url="dry-run://synthetic",
        requested_by_actor_type="system",
        requested_by_actor_identifier="test",
        request_reason="unit test",
        dry_run=True,
    )
    result = execute_fetch(fetcher, request)
    assert result.fetch_status == "success"
    assert result.content_type == "text/plain"
    assert result.checksum_sha256 is not None
    assert result.fetcher_name == "dry-run-fetcher"


def test_local_fixture_fetcher_reads_allowed_fixture():
    fetcher = LocalFixtureFetcher(fixture_root=_fixture_root())
    request = FetchRequest(
        requested_url="fixture://sample.txt",
        requested_by_actor_type="reviewer",
        requested_by_actor_identifier="qa",
        request_reason="validate fixture mode",
        dry_run=False,
        local_fixture_mode=True,
    )
    result = fetcher.fetch(request)
    assert result.fetch_status == "success"
    assert result.content_type == "text/plain"
    assert result.content_length and result.content_length > 0
    assert result.checksum_sha256 is not None
    assert result.storage_path is not None


def test_checksum_deterministic():
    payload = b"deterministic payload"
    assert sha256_bytes(payload) == sha256_bytes(payload)
    assert sha256_bytes(payload) != sha256_bytes(payload + b" ")


def test_content_type_detected_correctly():
    assert detect_content_type("sample.txt") == "text/plain"
    assert detect_content_type("sample.html") == "text/html"
    assert detect_content_type("sample.json") == "application/json"
    assert detect_content_type("sample.xml") == "application/xml"
    assert detect_content_type("sample.unknown") is None


def test_unsupported_content_type_rejected():
    fetcher = LocalFixtureFetcher(fixture_root=_fixture_root())
    request = FetchRequest(
        requested_url="fixture://sample.bin",
        requested_by_actor_type="reviewer",
        requested_by_actor_identifier=None,
        request_reason="unsupported fixture test",
        dry_run=False,
        local_fixture_mode=True,
    )
    result = fetcher.fetch(request)
    assert result.fetch_status == "failed"
    assert result.error_category == "unsupported_content_type"


def test_path_traversal_rejected():
    fetcher = LocalFixtureFetcher(fixture_root=_fixture_root())
    request = FetchRequest(
        requested_url="fixture://../secrets.txt",
        requested_by_actor_type="reviewer",
        requested_by_actor_identifier=None,
        request_reason="path traversal check",
        dry_run=False,
        local_fixture_mode=True,
    )
    result = fetcher.fetch(request)
    assert result.fetch_status == "blocked"
    assert result.error_category == "blocked"


def test_access_outside_fixture_root_rejected():
    fetcher = LocalFixtureFetcher(fixture_root=_fixture_root())
    request = FetchRequest(
        requested_url="file:///etc/passwd",
        requested_by_actor_type="reviewer",
        requested_by_actor_identifier=None,
        request_reason="outside root check",
        dry_run=False,
        local_fixture_mode=True,
    )
    result = fetcher.fetch(request)
    assert result.fetch_status == "blocked"
    assert result.error_category == "blocked"


def test_http_https_url_rejected():
    fetcher = LocalFixtureFetcher(fixture_root=_fixture_root())
    request = FetchRequest(
        requested_url="https://example.com/file.pdf",
        requested_by_actor_type="reviewer",
        requested_by_actor_identifier=None,
        request_reason="network guard",
        dry_run=False,
        local_fixture_mode=True,
    )
    result = fetcher.fetch(request)
    assert result.fetch_status == "blocked"
    assert result.error_category == "blocked"


def test_dry_run_safety_guard_enforced():
    fetcher = DryRunFetcher()
    request = FetchRequest(
        requested_url="dry-run://synthetic",
        requested_by_actor_type="system",
        requested_by_actor_identifier=None,
        request_reason="guard test",
        dry_run=False,
        local_fixture_mode=False,
    )
    with pytest.raises(FetchSafetyError):
        fetcher.fetch(request)


def test_max_content_size_enforced():
    fetcher = LocalFixtureFetcher(fixture_root=_fixture_root(), max_content_size_bytes=5)
    request = FetchRequest(
        requested_url="fixture://sample.txt",
        requested_by_actor_type="reviewer",
        requested_by_actor_identifier=None,
        request_reason="size limit test",
        dry_run=False,
        local_fixture_mode=True,
    )
    result = fetcher.fetch(request)
    assert result.fetch_status == "failed"
    assert result.error_category == "content_too_large"


def test_no_http_client_libraries_introduced():
    fetch_dir = Path(__file__).resolve().parents[1] / "app" / "services" / "fetch"
    forbidden_imports = ("requests", "httpx", "aiohttp", "urllib3")
    for path in fetch_dir.glob("*.py"):
        lowered = path.read_text().lower()
        for lib in forbidden_imports:
            assert f"import {lib}" not in lowered
            assert f"from {lib} import" not in lowered


@pytest.mark.integration
def test_no_source_versions_created(db_session):
    before = db_session.query(SourceVersion).count()
    fetcher = LocalFixtureFetcher(fixture_root=_fixture_root())
    request = FetchRequest(
        requested_url="fixture://sample.json",
        requested_by_actor_type="reviewer",
        requested_by_actor_identifier="qa",
        request_reason="ensure no source version creation",
        dry_run=False,
        local_fixture_mode=True,
    )
    result = fetcher.fetch(request)
    assert result.fetch_status == "success"
    after = db_session.query(SourceVersion).count()
    assert after == before


def test_fetch_result_fields_populated_correctly():
    fetcher = LocalFixtureFetcher(fixture_root=_fixture_root())
    request = FetchRequest(
        requested_url="fixture://sample.xml",
        requested_by_actor_type="reviewer",
        requested_by_actor_identifier="qa",
        request_reason="result shape validation",
        dry_run=False,
        local_fixture_mode=True,
    )
    result = fetcher.fetch(request)
    assert result.fetched_url == "fixture://sample.xml"
    assert result.final_url
    assert result.fetch_status == "success"
    assert result.fetched_at is not None
    assert result.content_type == "application/xml"
    assert result.content_length is not None
    assert result.checksum_sha256 is not None
    assert result.fetcher_name == "local-fixture-fetcher"
    assert result.fetcher_version == "0.1.0"

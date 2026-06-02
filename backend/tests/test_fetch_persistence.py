import pytest
from sqlalchemy import select

from app.core.datetime_utils import utc_now
from app.models.fetch_request import FetchRequest as FetchRequestModel
from app.models.fetch_result import FetchResult as FetchResultModel
from app.models.monitoring_candidate import MonitoringCandidate
from app.models.source_version import SourceVersion
from app.services.fetch import FetchRequest, FetchResult
from app.services.fetch.persistence import (
    FetchPersistenceError,
    create_fetch_request,
    create_persisted_fetch_request_from_contract,
    get_fetch_request,
    get_latest_fetch_result_for_request,
    list_fetch_results_for_request,
    persist_fetch_result,
    persist_result_from_contract,
)
from app.services.monitoring import create_allowlist_entry, create_monitoring_attempt, create_monitoring_candidate, create_monitoring_event
from tests.monitoring_test_helpers import seed_source_document

pytestmark = pytest.mark.integration


def _seed_candidate_graph(db_session):
    source_doc = seed_source_document(db_session)
    allowlist = create_allowlist_entry(
        db_session,
        jurisdiction="RW",
        authority_name="RRA",
        source_type="tax_authority_portal",
        base_url="https://example.test/rra",
        allowed_patterns_json=["/*"],
        blocked_patterns_json=[],
        monitoring_frequency="daily",
        status="active",
    )
    attempt = create_monitoring_attempt(
        db_session,
        source_allowlist_entry_id=allowlist.id,
        agent_name="dry-worker",
        agent_version="1.0.0",
        started_at=utc_now(),
    )
    event = create_monitoring_event(
        db_session,
        monitoring_attempt_id=attempt.id,
        source_registry_id=source_doc.id,
        source_url=allowlist.base_url,
        source_name="RRA",
        source_type=allowlist.source_type,
        detected_title="Fixture candidate",
        detected_url="https://example.test/rra/fixture",
        detected_at=utc_now(),
        detection_method="checksum",
        checksum_sha256="a" * 64,
        previous_checksum_sha256=None,
        change_type="new_document",
        confidence="low",
    )
    candidate = create_monitoring_candidate(db_session, monitoring_event_id=event.id)
    return allowlist, candidate


def test_fetch_request_creation(db_session):
    fetch_request = create_fetch_request(
        db_session,
        requested_url="fixture://sample.txt",
        requested_by_actor_type="test",
        requested_by_actor_identifier="suite",
        request_reason="persist request",
        dry_run=True,
        local_fixture_mode=False,
    )
    assert fetch_request.id is not None
    assert fetch_request.requested_url == "fixture://sample.txt"
    assert fetch_request.requested_by_actor_type == "test"


def test_fetch_result_persistence(db_session):
    fetch_request = create_fetch_request(
        db_session,
        requested_url="fixture://sample.json",
        requested_by_actor_type="worker",
        requested_by_actor_identifier=None,
        request_reason="persist success result",
        dry_run=True,
        local_fixture_mode=True,
    )
    result = persist_fetch_result(
        db_session,
        fetch_request_id=fetch_request.id,
        fetched_url="fixture://sample.json",
        final_url="/fixtures/sample.json",
        fetch_status="success",
        fetched_at=utc_now(),
        http_status_code=None,
        content_type="application/json",
        content_length=40,
        checksum_sha256="b" * 64,
        storage_backend="local_fixture",
        storage_path="/fixtures/sample.json",
        error_category=None,
        error_message=None,
        fetcher_name="local-fixture-fetcher",
        fetcher_version="0.1.0",
    )
    assert result.id is not None
    assert result.fetch_status == "success"
    assert result.fetcher_name == "local-fixture-fetcher"


def test_failed_fetch_result_persistence(db_session):
    fetch_request = create_fetch_request(
        db_session,
        requested_url="fixture://missing.pdf",
        requested_by_actor_type="test",
        requested_by_actor_identifier=None,
        request_reason="persist failed result",
        dry_run=True,
        local_fixture_mode=True,
    )
    result = persist_fetch_result(
        db_session,
        fetch_request_id=fetch_request.id,
        fetched_url="fixture://missing.pdf",
        final_url=None,
        fetch_status="failed",
        fetched_at=None,
        http_status_code=None,
        content_type=None,
        content_length=None,
        checksum_sha256=None,
        storage_backend=None,
        storage_path=None,
        error_category="unexpected_content",
        error_message="fixture not found",
        fetcher_name="local-fixture-fetcher",
        fetcher_version="0.1.0",
    )
    assert result.fetch_status == "failed"
    assert result.error_category == "unexpected_content"


def test_blocked_fetch_result_persistence(db_session):
    fetch_request = create_fetch_request(
        db_session,
        requested_url="https://example.com/file.pdf",
        requested_by_actor_type="worker",
        requested_by_actor_identifier=None,
        request_reason="persist blocked result",
        dry_run=True,
        local_fixture_mode=False,
    )
    result = persist_fetch_result(
        db_session,
        fetch_request_id=fetch_request.id,
        fetched_url="https://example.com/file.pdf",
        final_url=None,
        fetch_status="blocked",
        fetched_at=None,
        http_status_code=None,
        content_type=None,
        content_length=None,
        checksum_sha256=None,
        storage_backend="none",
        storage_path=None,
        error_category="access_denied",
        error_message="network access prohibited",
        fetcher_name="dry-run-fetcher",
        fetcher_version="0.1.0",
    )
    assert result.fetch_status == "blocked"
    assert result.error_message == "network access prohibited"


def test_multiple_results_for_same_request_append_correctly(db_session):
    fetch_request = create_fetch_request(
        db_session,
        requested_url="fixture://sample.xml",
        requested_by_actor_type="system",
        requested_by_actor_identifier=None,
        request_reason="append results",
        dry_run=True,
        local_fixture_mode=True,
    )
    first = persist_fetch_result(
        db_session,
        fetch_request_id=fetch_request.id,
        fetched_url="fixture://sample.xml",
        final_url="/fixtures/sample.xml",
        fetch_status="failed",
        fetched_at=None,
        http_status_code=None,
        content_type=None,
        content_length=None,
        checksum_sha256=None,
        storage_backend=None,
        storage_path=None,
        error_category="timeout",
        error_message="temporary timeout",
        fetcher_name="local-fixture-fetcher",
        fetcher_version="0.1.0",
    )
    second = persist_fetch_result(
        db_session,
        fetch_request_id=fetch_request.id,
        fetched_url="fixture://sample.xml",
        final_url="/fixtures/sample.xml",
        fetch_status="success",
        fetched_at=utc_now(),
        http_status_code=None,
        content_type="application/xml",
        content_length=100,
        checksum_sha256="c" * 64,
        storage_backend="local_fixture",
        storage_path="/fixtures/sample.xml",
        error_category=None,
        error_message=None,
        fetcher_name="local-fixture-fetcher",
        fetcher_version="0.1.0",
    )
    results = list_fetch_results_for_request(db_session, fetch_request_id=fetch_request.id)
    assert [r.id for r in results] == [first.id, second.id]


def test_latest_result_retrieval(db_session):
    fetch_request = create_fetch_request(
        db_session,
        requested_url="fixture://sample.html",
        requested_by_actor_type="system",
        requested_by_actor_identifier=None,
        request_reason="latest result check",
        dry_run=True,
        local_fixture_mode=True,
    )
    persist_fetch_result(
        db_session,
        fetch_request_id=fetch_request.id,
        fetched_url="fixture://sample.html",
        final_url=None,
        fetch_status="failed",
        fetched_at=None,
        http_status_code=None,
        content_type=None,
        content_length=None,
        checksum_sha256=None,
        storage_backend=None,
        storage_path=None,
        error_category="timeout",
        error_message="timeout",
        fetcher_name="local-fixture-fetcher",
        fetcher_version="0.1.0",
    )
    persist_fetch_result(
        db_session,
        fetch_request_id=fetch_request.id,
        fetched_url="fixture://sample.html",
        final_url="/fixtures/sample.html",
        fetch_status="success",
        fetched_at=utc_now(),
        http_status_code=None,
        content_type="text/html",
        content_length=128,
        checksum_sha256="d" * 64,
        storage_backend="local_fixture",
        storage_path="/fixtures/sample.html",
        error_category=None,
        error_message=None,
        fetcher_name="local-fixture-fetcher",
        fetcher_version="0.1.0",
    )
    latest = get_latest_fetch_result_for_request(db_session, fetch_request_id=fetch_request.id)
    assert latest is not None
    assert latest.fetch_status == "success"


def test_enum_validation(db_session):
    with pytest.raises(FetchPersistenceError):
        create_fetch_request(
            db_session,
            requested_url="fixture://sample.txt",
            requested_by_actor_type="invalid",
            requested_by_actor_identifier=None,
            request_reason="bad actor type",
            dry_run=True,
            local_fixture_mode=True,
        )
    fetch_request = create_fetch_request(
        db_session,
        requested_url="fixture://sample.txt",
        requested_by_actor_type="test",
        requested_by_actor_identifier=None,
        request_reason="enum checks",
        dry_run=True,
        local_fixture_mode=True,
    )
    with pytest.raises(FetchPersistenceError):
        persist_fetch_result(
            db_session,
            fetch_request_id=fetch_request.id,
            fetched_url="fixture://sample.txt",
            final_url=None,
            fetch_status="bad_status",
            fetched_at=None,
            http_status_code=None,
            content_type=None,
            content_length=None,
            checksum_sha256=None,
            storage_backend=None,
            storage_path=None,
            error_category=None,
            error_message=None,
            fetcher_name="local-fixture-fetcher",
            fetcher_version="0.1.0",
        )


def test_fk_integrity_with_monitoring_candidate_id_and_no_state_autochanges(db_session):
    allowlist, candidate = _seed_candidate_graph(db_session)
    before_state = db_session.get(MonitoringCandidate, candidate.id).candidate_state

    request = create_fetch_request(
        db_session,
        requested_url="fixture://sample.txt",
        requested_by_actor_type="worker",
        requested_by_actor_identifier="dry-worker",
        request_reason="fk integrity check",
        dry_run=True,
        local_fixture_mode=True,
        monitoring_candidate_id=candidate.id,
        source_allowlist_entry_id=allowlist.id,
    )
    assert request.monitoring_candidate_id == candidate.id

    persist_fetch_result(
        db_session,
        fetch_request_id=request.id,
        fetched_url="fixture://sample.txt",
        final_url="/fixtures/sample.txt",
        fetch_status="success",
        fetched_at=utc_now(),
        http_status_code=None,
        content_type="text/plain",
        content_length=36,
        checksum_sha256="e" * 64,
        storage_backend="local_fixture",
        storage_path="/fixtures/sample.txt",
        error_category=None,
        error_message=None,
        fetcher_name="local-fixture-fetcher",
        fetcher_version="0.1.0",
    )

    after_state = db_session.get(MonitoringCandidate, candidate.id).candidate_state
    assert after_state == before_state


def test_fk_integrity_invalid_monitoring_candidate_rejected(db_session):
    with pytest.raises(FetchPersistenceError):
        create_fetch_request(
            db_session,
            requested_url="fixture://sample.txt",
            requested_by_actor_type="test",
            requested_by_actor_identifier=None,
            request_reason="invalid candidate fk",
            dry_run=True,
            local_fixture_mode=True,
            monitoring_candidate_id="00000000-0000-0000-0000-000000000000",  # type: ignore[arg-type]
        )


def test_no_source_version_creation(db_session):
    before = db_session.query(SourceVersion).count()
    request = create_fetch_request(
        db_session,
        requested_url="fixture://sample.json",
        requested_by_actor_type="test",
        requested_by_actor_identifier=None,
        request_reason="no source version side effects",
        dry_run=True,
        local_fixture_mode=True,
    )
    persist_fetch_result(
        db_session,
        fetch_request_id=request.id,
        fetched_url="fixture://sample.json",
        final_url="/fixtures/sample.json",
        fetch_status="success",
        fetched_at=utc_now(),
        http_status_code=None,
        content_type="application/json",
        content_length=50,
        checksum_sha256="f" * 64,
        storage_backend="local_fixture",
        storage_path="/fixtures/sample.json",
        error_category=None,
        error_message=None,
        fetcher_name="local-fixture-fetcher",
        fetcher_version="0.1.0",
    )
    after = db_session.query(SourceVersion).count()
    assert after == before


def test_contract_mapping_helpers(db_session):
    contract_request = FetchRequest(
        requested_url="fixture://sample.xml",
        requested_by_actor_type="test",
        requested_by_actor_identifier="suite",
        request_reason="contract mapping request",
        dry_run=True,
        local_fixture_mode=True,
        monitoring_candidate_id=None,
        source_allowlist_entry_id=None,
        notes="note",
    )
    persisted_request = create_persisted_fetch_request_from_contract(
        db_session,
        fetch_request=contract_request,
    )
    assert persisted_request.requested_url == contract_request.requested_url

    contract_result = FetchResult(
        fetched_url="fixture://sample.xml",
        final_url="/fixtures/sample.xml",
        fetch_status="success",
        fetched_at=utc_now(),
        http_status_code=None,
        content_type="application/xml",
        content_length=120,
        checksum_sha256="1" * 64,
        storage_backend="local_fixture",
        storage_path="/fixtures/sample.xml",
        error_category=None,
        error_message=None,
        fetcher_name="local-fixture-fetcher",
        fetcher_version="0.1.0",
    )
    persisted_result = persist_result_from_contract(
        db_session,
        fetch_request_id=persisted_request.id,
        fetch_result=contract_result,
    )
    assert persisted_result.fetcher_name == "local-fixture-fetcher"


def test_get_fetch_request_returns_record(db_session):
    request = create_fetch_request(
        db_session,
        requested_url="fixture://sample.txt",
        requested_by_actor_type="test",
        requested_by_actor_identifier=None,
        request_reason="get request",
        dry_run=True,
        local_fixture_mode=True,
    )
    fetched = get_fetch_request(db_session, fetch_request_id=request.id)
    assert fetched is not None
    assert fetched.id == request.id


def test_records_exist_in_tables(db_session):
    request = create_fetch_request(
        db_session,
        requested_url="fixture://sample.txt",
        requested_by_actor_type="test",
        requested_by_actor_identifier=None,
        request_reason="table presence check",
        dry_run=True,
        local_fixture_mode=True,
    )
    persist_fetch_result(
        db_session,
        fetch_request_id=request.id,
        fetched_url="fixture://sample.txt",
        final_url="/fixtures/sample.txt",
        fetch_status="success",
        fetched_at=utc_now(),
        http_status_code=None,
        content_type="text/plain",
        content_length=36,
        checksum_sha256="2" * 64,
        storage_backend="local_fixture",
        storage_path="/fixtures/sample.txt",
        error_category=None,
        error_message=None,
        fetcher_name="local-fixture-fetcher",
        fetcher_version="0.1.0",
    )
    assert db_session.execute(select(FetchRequestModel)).scalar_one_or_none() is not None
    assert db_session.execute(select(FetchResultModel)).scalar_one_or_none() is not None

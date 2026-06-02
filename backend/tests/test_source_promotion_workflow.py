import pytest
from sqlalchemy import select

from app.core.datetime_utils import utc_now
from app.models.extracted_text import ExtractedText
from app.models.legal_object import LegalObject
from app.models.monitoring_candidate import MonitoringCandidate
from app.models.source_version import SourceVersion
from app.models.source_version_promotion import SourceVersionPromotion
from app.services.fetch.persistence import create_fetch_request, persist_fetch_result
from app.services.monitoring import (
    create_allowlist_entry,
    create_monitoring_attempt,
    create_monitoring_candidate,
    create_monitoring_event,
)
from app.services.source_promotion import SourceVersionPromotionRequest, promote_source_version
from tests.monitoring_test_helpers import seed_source_document

pytestmark = pytest.mark.integration


def _seed_success_fetch_result(db_session, *, checksum: str | None = "a" * 64, status: str = "success"):
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
        detected_title="Promotion candidate",
        detected_url="https://example.test/rra/doc",
        detected_at=utc_now(),
        detection_method="checksum",
        checksum_sha256="b" * 64,
        previous_checksum_sha256=None,
        change_type="new_document",
        confidence="low",
    )
    candidate = create_monitoring_candidate(db_session, monitoring_event_id=event.id)
    fetch_request = create_fetch_request(
        db_session,
        requested_url="fixture://sample.json",
        requested_by_actor_type="worker",
        requested_by_actor_identifier="dry-worker",
        request_reason="seed source promotion workflow",
        dry_run=True,
        local_fixture_mode=True,
        monitoring_candidate_id=candidate.id,
        source_allowlist_entry_id=allowlist.id,
    )
    fetch_result = persist_fetch_result(
        db_session,
        fetch_request_id=fetch_request.id,
        fetched_url="fixture://sample.json",
        final_url="/fixtures/sample.json",
        fetch_status=status,
        fetched_at=utc_now(),
        http_status_code=None,
        content_type="application/json",
        content_length=100,
        checksum_sha256=checksum,
        storage_backend="local_fixture",
        storage_path="/fixtures/sample.json",
        error_category=None,
        error_message=None,
        fetcher_name="local-fixture-fetcher",
        fetcher_version="0.1.0",
    )
    return source_doc, candidate, fetch_result


def test_successful_promotion_creates_source_version(db_session):
    source_doc, candidate, fetch_result = _seed_success_fetch_result(db_session, checksum="c" * 64)
    request = SourceVersionPromotionRequest(
        monitoring_candidate_id=candidate.id,
        fetch_result_id=fetch_result.id,
        source_document_id=source_doc.id,
        requested_by_actor_type="admin",
        requested_by_actor_identifier="qa-reviewer",
        promotion_reason="approved artifact to canonical memory",
        proposed_version_label="2026-06-02-review-1",
        publication_date=None,
        effective_from=None,
        effective_to=None,
        notes="manual review approved",
    )
    result = promote_source_version(db_session, request=request)
    assert result.promotion_status == "approved"
    assert result.source_version_id is not None

    created = db_session.get(SourceVersion, result.source_version_id)
    assert created is not None
    assert created.source_document_id == source_doc.id
    assert created.checksum_sha256 == "c" * 64
    assert created.version_label == "2026-06-02-review-1"
    assert created.effective_from is None
    assert created.effective_to is None


def test_duplicate_rejection_when_checksum_already_exists(db_session):
    source_doc, candidate, fetch_result = _seed_success_fetch_result(db_session, checksum="d" * 64)
    first = promote_source_version(
        db_session,
        request=SourceVersionPromotionRequest(
            monitoring_candidate_id=candidate.id,
            fetch_result_id=fetch_result.id,
            source_document_id=source_doc.id,
            requested_by_actor_type="admin",
            promotion_reason="first promote",
        ),
    )
    assert first.promotion_status == "approved"

    second = promote_source_version(
        db_session,
        request=SourceVersionPromotionRequest(
            monitoring_candidate_id=candidate.id,
            fetch_result_id=fetch_result.id,
            source_document_id=source_doc.id,
            requested_by_actor_type="admin",
            promotion_reason="second promote duplicate",
        ),
    )
    assert second.promotion_status == "duplicate_rejected"
    assert second.source_version_id is None


def test_failed_fetch_result_rejected(db_session):
    source_doc, candidate, fetch_result = _seed_success_fetch_result(
        db_session, checksum="e" * 64, status="failed"
    )
    result = promote_source_version(
        db_session,
        request=SourceVersionPromotionRequest(
            monitoring_candidate_id=candidate.id,
            fetch_result_id=fetch_result.id,
            source_document_id=source_doc.id,
            requested_by_actor_type="admin",
            promotion_reason="attempt failed fetch promotion",
        ),
    )
    assert result.promotion_status == "rejected"
    assert "fetch_result must be successful" in " ".join(result.validation_errors)


def test_missing_source_document_rejected(db_session):
    _, candidate, fetch_result = _seed_success_fetch_result(db_session, checksum="f" * 64)
    result = promote_source_version(
        db_session,
        request=SourceVersionPromotionRequest(
            monitoring_candidate_id=candidate.id,
            fetch_result_id=fetch_result.id,
            source_document_id="00000000-0000-0000-0000-000000000000",  # type: ignore[arg-type]
            requested_by_actor_type="admin",
            promotion_reason="invalid source document",
        ),
    )
    assert result.promotion_status == "rejected"
    assert "source_document not found" in " ".join(result.validation_errors)


def test_checksum_validation_enforced(db_session):
    source_doc, candidate, fetch_result = _seed_success_fetch_result(db_session, checksum=None)
    result = promote_source_version(
        db_session,
        request=SourceVersionPromotionRequest(
            monitoring_candidate_id=candidate.id,
            fetch_result_id=fetch_result.id,
            source_document_id=source_doc.id,
            requested_by_actor_type="admin",
            promotion_reason="checksum required validation",
        ),
    )
    assert result.promotion_status == "rejected"
    assert "checksum is required for promotion" in " ".join(result.validation_errors)


def test_append_only_promotion_history(db_session):
    source_doc, candidate, fetch_result = _seed_success_fetch_result(db_session, checksum="1" * 64)
    promote_source_version(
        db_session,
        request=SourceVersionPromotionRequest(
            monitoring_candidate_id=candidate.id,
            fetch_result_id=fetch_result.id,
            source_document_id=source_doc.id,
            requested_by_actor_type="admin",
            promotion_reason="first history row",
        ),
    )
    promote_source_version(
        db_session,
        request=SourceVersionPromotionRequest(
            monitoring_candidate_id=candidate.id,
            fetch_result_id=fetch_result.id,
            source_document_id=source_doc.id,
            requested_by_actor_type="admin",
            promotion_reason="second history row",
        ),
    )
    rows = db_session.execute(select(SourceVersionPromotion)).scalars().all()
    assert len(rows) == 2


def test_no_automatic_extraction_or_legal_object_creation(db_session):
    source_doc, candidate, fetch_result = _seed_success_fetch_result(db_session, checksum="2" * 64)
    extracted_before = db_session.query(ExtractedText).count()
    legal_before = db_session.query(LegalObject).count()

    _ = promote_source_version(
        db_session,
        request=SourceVersionPromotionRequest(
            monitoring_candidate_id=candidate.id,
            fetch_result_id=fetch_result.id,
            source_document_id=source_doc.id,
            requested_by_actor_type="admin",
            promotion_reason="check no auto ingestion side effects",
        ),
    )

    extracted_after = db_session.query(ExtractedText).count()
    legal_after = db_session.query(LegalObject).count()
    assert extracted_before == extracted_after
    assert legal_before == legal_after


def test_temporal_no_inference_and_provenance_preserved(db_session):
    source_doc, candidate, fetch_result = _seed_success_fetch_result(db_session, checksum="3" * 64)
    result = promote_source_version(
        db_session,
        request=SourceVersionPromotionRequest(
            monitoring_candidate_id=candidate.id,
            fetch_result_id=fetch_result.id,
            source_document_id=source_doc.id,
            requested_by_actor_type="admin",
            requested_by_actor_identifier="reviewer-1",
            promotion_reason="temporal no inference check",
            effective_from=None,
            effective_to=None,
        ),
    )
    created = db_session.get(SourceVersion, result.source_version_id)
    assert created is not None
    assert created.effective_from is None
    assert created.effective_to is None
    promotion = db_session.execute(
        select(SourceVersionPromotion).where(SourceVersionPromotion.source_version_id == created.id)
    ).scalar_one()
    assert promotion.fetch_result_id == fetch_result.id
    assert promotion.monitoring_candidate_id == candidate.id
    assert promotion.requested_by_actor_type == "admin"


def test_fk_integrity_and_no_candidate_state_auto_change(db_session):
    source_doc, candidate, fetch_result = _seed_success_fetch_result(db_session, checksum="4" * 64)
    before = db_session.get(MonitoringCandidate, candidate.id).candidate_state

    _ = promote_source_version(
        db_session,
        request=SourceVersionPromotionRequest(
            monitoring_candidate_id=candidate.id,
            fetch_result_id=fetch_result.id,
            source_document_id=source_doc.id,
            requested_by_actor_type="admin",
            promotion_reason="fk integrity and state freeze",
        ),
    )

    after = db_session.get(MonitoringCandidate, candidate.id).candidate_state
    assert before == after

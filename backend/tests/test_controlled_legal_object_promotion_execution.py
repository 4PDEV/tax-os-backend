import pytest
from sqlalchemy import inspect, select

from app.core.datetime_utils import utc_now
from app.models.legal_object import LegalObject
from app.models.legal_object_promotion_result import LegalObjectPromotionResult
from app.models.legal_object_version import LegalObjectVersion
from app.models.parsed_structure import ParsedStructure
from app.models.source_version import SourceVersion
from app.services.legal_object_promotion import (
    create_promotion_request,
    legal_object_id_for_parsed_structure,
)
from app.services.legal_object_promotion.materialization import materialize_legal_object_from_parsed_structure
from app.workers.legal_object_promotion import (
    CONTROLLED_LEGAL_OBJECT_PROMOTION_PROVIDER_NAME,
    LegalObjectPromotionProviderResult,
    LegalObjectPromotionWorker,
    LegalObjectPromotionWorkerError,
    run_controlled_legal_object_promotion,
    run_legal_object_promotion_dry_run,
)
from app.workers.legal_object_promotion.controlled_provider import (
    ControlledLegalObjectPromotionProvider,
)
from app.workers.legal_object_promotion.dry_run_provider import LegalObjectPromotionProvider
from tests.test_legal_object_promotion_persistence import _seed_parsed_structure

pytestmark = pytest.mark.integration


class FailingPromotionProvider(LegalObjectPromotionProvider):
    def run_promotion(self, db, parsed_structure, promotion_request):
        _ = db, parsed_structure, promotion_request
        return LegalObjectPromotionProviderResult(
            success=False,
            error_category="promotion_pipeline_unavailable",
            error_message="synthetic provider failure",
        )


def test_non_controlled_runner_rejected():
    with pytest.raises(LegalObjectPromotionWorkerError):
        run_controlled_legal_object_promotion(None, controlled_promotion=False)  # type: ignore[arg-type]


def test_controlled_promotion_creates_legal_object_and_version(db_session):
    parsed, extracted = _seed_parsed_structure(db_session)
    request = create_promotion_request(
        db_session,
        parsed_structure_id=parsed.id,
        source_version_id=extracted.source_version_id,
        requested_by_actor_type="worker",
        promotion_reason="controlled promotion",
    )

    summary = run_controlled_legal_object_promotion(db_session, controlled_promotion=True)

    assert summary.requests_processed == 1
    assert summary.results_created == 2
    assert summary.failures == 0

    expected_id = legal_object_id_for_parsed_structure(parsed.id)
    legal_object = db_session.get(LegalObject, expected_id)
    assert legal_object is not None
    assert legal_object.canonical_path

    version = db_session.execute(
        select(LegalObjectVersion).where(LegalObjectVersion.legal_object_id == expected_id)
    ).scalar_one()
    assert version.source_version_id == extracted.source_version_id
    assert version.structural_unit_id == str(parsed.id)
    assert version.text_hash == parsed.structure_hash
    assert legal_object.current_version_id == version.legal_object_version_id

    latest = (
        db_session.execute(
            select(LegalObjectPromotionResult)
            .where(LegalObjectPromotionResult.legal_object_promotion_request_id == request.id)
            .order_by(LegalObjectPromotionResult.created_at.desc())
        )
        .scalars()
        .first()
    )
    assert latest is not None
    assert latest.promotion_status == "promoted"
    assert latest.legal_object_id == expected_id
    assert latest.promoted_at is not None


def test_provenance_and_temporal_fields_preserved(db_session):
    parsed, extracted = _seed_parsed_structure(db_session)
    version = db_session.get(SourceVersion, extracted.source_version_id)
    version.effective_from = utc_now().date()
    version.effective_to = utc_now().date()
    db_session.flush()

    create_promotion_request(
        db_session,
        parsed_structure_id=parsed.id,
        source_version_id=extracted.source_version_id,
        requested_by_actor_type="worker",
        promotion_reason="temporal preservation",
    )
    run_controlled_legal_object_promotion(db_session, controlled_promotion=True)

    stored_version = db_session.execute(select(LegalObjectVersion)).scalar_one()
    assert stored_version.effective_from == version.effective_from
    assert stored_version.effective_to == version.effective_to
    assert "parsed_structure=" in (stored_version.object_title or "")
    assert "structure_hash=" in (stored_version.object_title or "")


def test_promoted_request_not_reprocessed(db_session):
    parsed, extracted = _seed_parsed_structure(db_session)
    create_promotion_request(
        db_session,
        parsed_structure_id=parsed.id,
        source_version_id=extracted.source_version_id,
        requested_by_actor_type="worker",
        promotion_reason="first promotion",
    )
    first = run_controlled_legal_object_promotion(db_session, controlled_promotion=True)
    assert first.requests_processed == 1

    second = run_controlled_legal_object_promotion(db_session, controlled_promotion=True)
    assert second.requests_skipped == 1
    assert db_session.query(LegalObjectVersion).count() == 1


def test_force_repromotion_appends_new_version(db_session):
    parsed, extracted = _seed_parsed_structure(db_session)
    create_promotion_request(
        db_session,
        parsed_structure_id=parsed.id,
        source_version_id=extracted.source_version_id,
        requested_by_actor_type="worker",
        promotion_reason="initial",
        force_repromotion=False,
    )
    run_controlled_legal_object_promotion(db_session, controlled_promotion=True)

    replay = create_promotion_request(
        db_session,
        parsed_structure_id=parsed.id,
        source_version_id=extracted.source_version_id,
        requested_by_actor_type="worker",
        promotion_reason="replay",
        force_repromotion=True,
    )
    second = run_controlled_legal_object_promotion(db_session, controlled_promotion=True)
    assert second.requests_processed == 1
    assert db_session.query(LegalObject).count() == 1
    assert db_session.query(LegalObjectVersion).count() == 2

    legal_object_id = legal_object_id_for_parsed_structure(parsed.id)
    versions = (
        db_session.execute(
            select(LegalObjectVersion)
            .where(LegalObjectVersion.legal_object_id == legal_object_id)
            .order_by(LegalObjectVersion.created_at.asc())
        )
        .scalars()
        .all()
    )
    assert versions[0].text_hash == parsed.structure_hash
    assert versions[1].text_hash != versions[0].text_hash

    latest_result = (
        db_session.execute(
            select(LegalObjectPromotionResult)
            .where(LegalObjectPromotionResult.legal_object_promotion_request_id == replay.id)
            .order_by(LegalObjectPromotionResult.created_at.desc())
        )
        .scalars()
        .first()
    )
    assert latest_result is not None
    assert latest_result.promotion_status == "promoted"


def test_duplicate_materialization_blocked(db_session):
    parsed, extracted = _seed_parsed_structure(db_session)
    request = create_promotion_request(
        db_session,
        parsed_structure_id=parsed.id,
        source_version_id=extracted.source_version_id,
        requested_by_actor_type="worker",
        promotion_reason="duplicate materialization",
    )
    materialize_legal_object_from_parsed_structure(
        db_session, parsed_structure=parsed, promotion_request=request
    )
    with pytest.raises(ValueError, match="duplicate_promotion"):
        materialize_legal_object_from_parsed_structure(
            db_session, parsed_structure=parsed, promotion_request=request
        )


def test_provider_failure_records_failed_without_legal_object(db_session):
    parsed, extracted = _seed_parsed_structure(db_session)
    create_promotion_request(
        db_session,
        parsed_structure_id=parsed.id,
        source_version_id=extracted.source_version_id,
        requested_by_actor_type="worker",
        promotion_reason="failure path",
    )
    worker = LegalObjectPromotionWorker(
        provider=FailingPromotionProvider(),
        mode="controlled_promotion",
    )
    summary = worker.run(db_session)
    assert summary.failures == 1
    assert db_session.query(LegalObject).count() == 0

    latest = (
        db_session.execute(
            select(LegalObjectPromotionResult).order_by(LegalObjectPromotionResult.created_at.desc())
        )
        .scalars()
        .first()
    )
    assert latest is not None
    assert latest.promotion_status == "failed"


def test_dry_run_still_passes_after_controlled_mode(db_session):
    parsed, extracted = _seed_parsed_structure(db_session)
    create_promotion_request(
        db_session,
        parsed_structure_id=parsed.id,
        source_version_id=extracted.source_version_id,
        requested_by_actor_type="test",
        promotion_reason="dry-run regression",
    )
    summary = run_legal_object_promotion_dry_run(db_session, dry_run=True)
    assert summary.requests_processed == 1
    assert db_session.query(LegalObject).count() == 0

    latest = (
        db_session.execute(
            select(LegalObjectPromotionResult)
            .order_by(LegalObjectPromotionResult.created_at.desc())
        )
        .scalars()
        .first()
    )
    assert latest.promotion_status == "skipped"
    assert latest.legal_object_id is None


def test_no_citation_or_answer_tables(db_session, engine):
    parsed, extracted = _seed_parsed_structure(db_session)
    create_promotion_request(
        db_session,
        parsed_structure_id=parsed.id,
        source_version_id=extracted.source_version_id,
        requested_by_actor_type="test",
        promotion_reason="boundary",
    )
    run_controlled_legal_object_promotion(db_session, controlled_promotion=True)
    tables = set(inspect(engine).get_table_names())
    citation_tables = {name for name in tables if "citation" in name}
    assert citation_tables <= {
        "citation_assembly_governance_requests",
        "citation_assembly_governance_results",
    }
    assert "citations" not in tables
    assert not any("answer" in name for name in tables)


def test_no_promotion_ai_imports_introduced():
    from pathlib import Path

    worker_dir = (
        Path(__file__).resolve().parents[1] / "app" / "workers" / "legal_object_promotion"
    )
    service_dir = (
        Path(__file__).resolve().parents[1] / "app" / "services" / "legal_object_promotion"
    )
    forbidden = (
        "requests",
        "httpx",
        "openai",
        "anthropic",
        "transformers",
        "spacy",
        "nltk",
    )
    for base in (worker_dir, service_dir):
        for path in base.glob("*.py"):
            content = path.read_text().lower()
            for lib in forbidden:
                assert f"import {lib}" not in content
                assert f"from {lib} import" not in content


def test_append_only_legal_object_row_not_replaced_on_replay(db_session):
    parsed, extracted = _seed_parsed_structure(db_session)
    create_promotion_request(
        db_session,
        parsed_structure_id=parsed.id,
        source_version_id=extracted.source_version_id,
        requested_by_actor_type="worker",
        promotion_reason="v1",
        force_repromotion=False,
    )
    run_controlled_legal_object_promotion(db_session, controlled_promotion=True)
    legal_object_id = legal_object_id_for_parsed_structure(parsed.id)
    first_object = db_session.get(LegalObject, legal_object_id)
    first_created_at = first_object.created_at

    create_promotion_request(
        db_session,
        parsed_structure_id=parsed.id,
        source_version_id=extracted.source_version_id,
        requested_by_actor_type="worker",
        promotion_reason="v2",
        force_repromotion=True,
    )
    run_controlled_legal_object_promotion(db_session, controlled_promotion=True)
    second_object = db_session.get(LegalObject, legal_object_id)
    assert second_object.created_at == first_created_at
    assert db_session.query(LegalObject).count() == 1

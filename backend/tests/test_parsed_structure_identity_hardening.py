import pytest
from sqlalchemy.exc import IntegrityError

from app.core.datetime_utils import utc_now
from app.models.parsed_structure import ParsedStructure
from app.models.parser_run import ParserRun
from app.services.ingestion.enums import ParserRunStatus, STRUCTURE_TYPE_STRUCTURAL_UNITS
from app.services.ingestion.errors import IngestionPersistenceError
from app.services.ingestion.hashing import sha256_structure
from app.services.ingestion.parser_persistence import persist_parsed_structure
from app.services.parsing_trigger import create_parsing_trigger_request
from app.workers.parsing import run_controlled_structural_parsing
from tests.test_controlled_parsing_execution import SAMPLE_LEGAL_TEXT, _seed_extracted_text, _trigger

pytestmark = pytest.mark.integration

_UNITS = [
    {
        "unit_type": "section",
        "unit_label": "15",
        "unit_title": None,
        "full_heading": "Section 15",
        "parent_unit_id": None,
        "hierarchy_level": 1,
        "start_offset": 0,
        "end_offset": 10,
        "raw_text": "Section 15",
    }
]


def _seed_parser_run(db_session):
    extracted = _seed_extracted_text(db_session)
    run = ParserRun(
        extraction_run_id=extracted.extraction_run_id,
        parser_name="test_parser",
        parser_version="1.0.0",
        parser_status=ParserRunStatus.SUCCESS.value,
        started_at=utc_now(),
        completed_at=utc_now(),
    )
    db_session.add(run)
    db_session.flush()
    return run, extracted


def test_service_rejects_duplicate_parsed_structure_for_same_parser_run(db_session):
    run, _ = _seed_parser_run(db_session)
    persist_parsed_structure(db_session, parser_run_id=run.id, structure_units=_UNITS)
    with pytest.raises(IngestionPersistenceError, match="already exists"):
        persist_parsed_structure(db_session, parser_run_id=run.id, structure_units=_UNITS)


def test_db_rejects_duplicate_parsed_structure_for_same_parser_run(db_session):
    run, extracted = _seed_parser_run(db_session)
    structure_hash = sha256_structure(_UNITS)
    first = ParsedStructure(
        parser_run_id=run.id,
        source_version_id=extracted.source_version_id,
        structure_type=STRUCTURE_TYPE_STRUCTURAL_UNITS,
        structure_json={"structure_type": STRUCTURE_TYPE_STRUCTURAL_UNITS, "units": _UNITS},
        structure_hash=structure_hash,
    )
    db_session.add(first)
    db_session.flush()

    second = ParsedStructure(
        parser_run_id=run.id,
        source_version_id=extracted.source_version_id,
        structure_type=STRUCTURE_TYPE_STRUCTURAL_UNITS,
        structure_json={"structure_type": STRUCTURE_TYPE_STRUCTURAL_UNITS, "units": _UNITS},
        structure_hash=structure_hash,
    )
    db_session.add(second)
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_force_reparse_creates_new_parser_run_and_parsed_structure(db_session):
    extracted = _seed_extracted_text(db_session)
    _trigger(db_session, extracted, force_reparse=False)
    _ = run_controlled_structural_parsing(db_session, controlled_structural=True)

    _trigger(db_session, extracted, force_reparse=True, trigger_reason="structure replay")
    second = run_controlled_structural_parsing(db_session, controlled_structural=True)
    assert second.parser_runs_created == 1
    assert db_session.query(ParserRun).count() == 2
    assert db_session.query(ParsedStructure).count() == 2


def test_structure_hash_stable_for_identical_units():
    hash_one = sha256_structure(_UNITS)
    hash_two = sha256_structure(list(_UNITS))
    assert hash_one == hash_two


def test_structure_hash_excludes_volatile_metadata():
    """Reuses ingestion hashing contract — volatile keys must not affect hash."""
    from app.services.ingestion.hashing import canonical_structure_units_for_hash

    units = [{**_UNITS[0], "unit_id": "a", "detected_at": "2026-01-01"}]
    units_alt = [{**_UNITS[0], "unit_id": "b", "detected_at": "2099-12-31"}]
    assert sha256_structure(units) == sha256_structure(units_alt)
    canonical = canonical_structure_units_for_hash(units)
    assert "unit_id" not in canonical[0]
    assert "detected_at" not in canonical[0]

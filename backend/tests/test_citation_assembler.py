from datetime import date
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.models.legal_object import LegalObject
from app.models.legal_object_version import LegalObjectVersion
from app.services.citation import (
    AuthorityType,
    CitationAssembler,
    CitationAssemblyRequest,
    CitationFormatter,
    LegalObjectVersionMismatchError,
    MissingLocationReferenceError,
    MissingSourceVersionError,
    SourceDocumentMismatchError,
)
from app.services.citation.hash import compute_citation_hash
from app.services.citation.location import build_location_reference
from tests.retrieval_test_helpers import (
    add_version_row,
    make_candidate,
    persist_candidate,
    seed_source_version,
    set_version_effective_dates,
)


def test_assembly_request_forbids_extra_fields():
    with pytest.raises(ValidationError):
        CitationAssemblyRequest(
            legal_object_id="lo_test",
            legal_object_version_id=uuid4(),
            extra_field=True,
        )


def test_build_location_reference_section():
    assert build_location_reference(object_type="section", object_label="15") == "Section 15"


def test_build_location_reference_rejects_empty_label():
    with pytest.raises(ValueError):
        build_location_reference(object_type="section", object_label="   ")


def test_citation_hash_deterministic():
    version_id = uuid4()
    legal_object_version_id = uuid4()
    first = compute_citation_hash(
        source_version_id=version_id,
        legal_object_id="lo_abc",
        legal_object_version_id=legal_object_version_id,
        location_reference="Section 15",
    )
    second = compute_citation_hash(
        source_version_id=version_id,
        legal_object_id="lo_abc",
        legal_object_version_id=legal_object_version_id,
        location_reference="Section 15",
    )
    assert first == second
    assert len(first) == 64


def test_citation_hash_differs_by_legal_object_version_id():
    source_version_id = uuid4()
    shared = dict(
        source_version_id=source_version_id,
        legal_object_id="lo_abc",
        location_reference="Section 15",
    )
    first = compute_citation_hash(legal_object_version_id=uuid4(), **shared)
    second = compute_citation_hash(legal_object_version_id=uuid4(), **shared)
    assert first != second


@pytest.mark.integration
def test_citation_result_includes_legal_object_version_id(db_session):
    _, _, _, version = seed_source_version(db_session)
    candidate = persist_candidate(
        db_session,
        make_candidate(source_version_id=str(version.id)),
    )
    legal_object = db_session.query(LegalObject).filter_by(
        legal_object_id=candidate.legal_object_id
    ).one()
    legal_object_version = db_session.query(LegalObjectVersion).filter_by(
        legal_object_id=candidate.legal_object_id
    ).one()

    result = CitationAssembler().assemble(
        db_session,
        legal_object,
        legal_object_version_id=legal_object_version.legal_object_version_id,
    )
    assert result.legal_object_version_id == legal_object_version.legal_object_version_id


@pytest.mark.integration
def test_different_legal_object_versions_produce_different_citation_identity(db_session):
    _, _, _, version = seed_source_version(db_session)
    candidate = persist_candidate(
        db_session,
        make_candidate(source_version_id=str(version.id)),
    )
    first_version = db_session.query(LegalObjectVersion).filter_by(
        legal_object_id=candidate.legal_object_id
    ).one()

    add_version_row(
        db_session,
        legal_object_id=candidate.legal_object_id,
        source_version_id=version.id,
        raw_text="Alternate version text.",
        object_label="Section 15",
        structural_unit_id="su-0001",
        effective_from=date(2025, 1, 1),
        effective_to=date(2025, 12, 31),
    )
    second_version = (
        db_session.query(LegalObjectVersion)
        .filter(LegalObjectVersion.legal_object_id == candidate.legal_object_id)
        .filter(LegalObjectVersion.legal_object_version_id != first_version.legal_object_version_id)
        .one()
    )
    legal_object = db_session.query(LegalObject).filter_by(
        legal_object_id=candidate.legal_object_id
    ).one()

    first_result = CitationAssembler().assemble(
        db_session,
        legal_object,
        legal_object_version_id=first_version.legal_object_version_id,
    )
    second_result = CitationAssembler().assemble(
        db_session,
        legal_object,
        legal_object_version_id=second_version.legal_object_version_id,
    )

    assert first_result.legal_object_id == second_result.legal_object_id
    assert first_result.legal_object_version_id != second_result.legal_object_version_id
    assert first_result.citation_hash != second_result.citation_hash
    assert first_result.citation_id != second_result.citation_id


def test_source_document_mismatch_fails():
    assembler = CitationAssembler()
    legal_object = MagicMock(source_document_id=uuid4())
    version = MagicMock(
        object_label="Section 15",
        source_version_id=uuid4(),
        legal_object_version_id=uuid4(),
    )
    source_version = MagicMock(
        id=version.source_version_id,
        source_document_id=uuid4(),
        version_label="v1",
        publication_date=None,
        effective_from=None,
        effective_to=None,
    )
    db = MagicMock()
    db.query.return_value.filter.return_value.first.side_effect = [
        source_version,
        MagicMock(
            id=legal_object.source_document_id,
            source_type="law",
            authority_level="national",
            title="VAT Law",
            official_reference=None,
        ),
    ]

    with pytest.raises(SourceDocumentMismatchError):
        assembler._assemble_from_version(db, legal_object, version)


@pytest.mark.integration
def test_citation_generation(db_session):
    _, _, document, version = seed_source_version(db_session)
    version.version_label = "Finance Act 2024 Amendment"
    db_session.flush()

    candidate = persist_candidate(
        db_session,
        make_candidate(source_version_id=str(version.id)),
    )
    set_version_effective_dates(
        db_session,
        candidate.legal_object_id,
        effective_from=date(2024, 7, 1),
        effective_to=date(2024, 12, 31),
    )
    legal_object = db_session.query(LegalObject).filter_by(
        legal_object_id=candidate.legal_object_id
    ).one()
    legal_object_version = db_session.query(LegalObjectVersion).filter_by(
        legal_object_id=candidate.legal_object_id
    ).one()

    result = CitationAssembler().assemble(
        db_session,
        legal_object,
        legal_object_version_id=legal_object_version.legal_object_version_id,
    )

    assert result.source_document_id == document.id
    assert result.source_version_id == version.id
    assert result.legal_object_id == candidate.legal_object_id
    assert result.legal_object_version_id == legal_object_version.legal_object_version_id
    assert result.authority_type == AuthorityType.STATUTE
    assert result.source_title == "VAT Law"
    assert result.location_reference == "Section 15"
    assert result.citation_hash
    assert result.citation_id.startswith("cit_")
    assert "VAT Law," in result.citation_text
    assert "Section 15," in result.citation_text
    assert "Finance Act 2024 Amendment Version." in result.citation_text
    assert result.assembler_version == "1.0.0"


@pytest.mark.integration
def test_source_traceability_enforcement_missing_version(db_session):
    _, _, _, version = seed_source_version(db_session)
    candidate = persist_candidate(
        db_session,
        make_candidate(source_version_id=str(version.id)),
    )
    legal_object = db_session.query(LegalObject).filter_by(
        legal_object_id=candidate.legal_object_id
    ).one()

    with pytest.raises(MissingSourceVersionError):
        CitationAssembler().assemble(
            db_session,
            legal_object,
            legal_object_version_id=uuid4(),
        )


def test_source_traceability_version_mismatch_unit():
    assembler = CitationAssembler()
    version_id = uuid4()
    version = MagicMock(
        legal_object_version_id=version_id,
        legal_object_id="lo_object_a",
        source_version_id=uuid4(),
    )
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = version

    with pytest.raises(LegalObjectVersionMismatchError):
        assembler._load_version(
            db,
            legal_object_id="lo_object_b",
            legal_object_version_id=version_id,
        )


@pytest.mark.integration
def test_missing_location_reference(db_session):
    _, _, _, version = seed_source_version(db_session)
    candidate = persist_candidate(
        db_session,
        make_candidate(source_version_id=str(version.id)),
    )
    legal_object = db_session.query(LegalObject).filter_by(
        legal_object_id=candidate.legal_object_id
    ).one()
    legal_object_version = db_session.query(LegalObjectVersion).filter_by(
        legal_object_id=candidate.legal_object_id
    ).one()
    legal_object_version.object_label = "   "
    db_session.flush()

    with pytest.raises(MissingLocationReferenceError):
        CitationAssembler().assemble(
            db_session,
            legal_object,
            legal_object_version_id=legal_object_version.legal_object_version_id,
        )


@pytest.mark.integration
def test_version_awareness_uses_explicit_pin_not_implicit_latest(db_session):
    _, _, document, version = seed_source_version(db_session)
    version.version_label = "Pinned Version A"
    db_session.flush()

    candidate = persist_candidate(
        db_session,
        make_candidate(source_version_id=str(version.id)),
    )
    pinned_version = db_session.query(LegalObjectVersion).filter_by(
        legal_object_id=candidate.legal_object_id
    ).one()

    add_version_row(
        db_session,
        legal_object_id=candidate.legal_object_id,
        source_version_id=version.id,
        raw_text="Later version text for overlap.",
        object_label="Section 15",
        structural_unit_id="su-0001",
        effective_from=date(2025, 1, 1),
        effective_to=date(2025, 12, 31),
    )
    legal_object = db_session.query(LegalObject).filter_by(
        legal_object_id=candidate.legal_object_id
    ).one()
    legal_object.current_version_id = (
        db_session.query(LegalObjectVersion)
        .filter(LegalObjectVersion.legal_object_id == candidate.legal_object_id)
        .order_by(LegalObjectVersion.created_at.desc())
        .first()
        .legal_object_version_id
    )
    db_session.flush()

    result = CitationAssembler().assemble(
        db_session,
        legal_object,
        legal_object_version_id=pinned_version.legal_object_version_id,
    )

    assert result.source_version_id == version.id
    assert "Pinned Version A Version." in result.citation_text
    assert result.source_document_id == document.id


@pytest.mark.integration
def test_assemble_by_request(db_session):
    _, _, _, version = seed_source_version(db_session)
    candidate = persist_candidate(
        db_session,
        make_candidate(source_version_id=str(version.id)),
    )
    legal_object_version = db_session.query(LegalObjectVersion).filter_by(
        legal_object_id=candidate.legal_object_id
    ).one()

    result = CitationAssembler().assemble_by_request(
        db_session,
        CitationAssemblyRequest(
            legal_object_id=candidate.legal_object_id,
            legal_object_version_id=legal_object_version.legal_object_version_id,
        ),
    )
    assert result.location_reference == "Section 15"


@pytest.mark.integration
def test_no_citation_persistence(db_session):
    _, _, _, version = seed_source_version(db_session)
    candidate = persist_candidate(
        db_session,
        make_candidate(source_version_id=str(version.id)),
    )
    legal_object = db_session.query(LegalObject).filter_by(
        legal_object_id=candidate.legal_object_id
    ).one()
    legal_object_version = db_session.query(LegalObjectVersion).filter_by(
        legal_object_id=candidate.legal_object_id
    ).one()
    version_count_before = db_session.query(LegalObjectVersion).count()

    CitationAssembler().assemble(
        db_session,
        legal_object,
        legal_object_version_id=legal_object_version.legal_object_version_id,
    )

    assert db_session.query(LegalObjectVersion).count() == version_count_before
    table_names = db_session.bind.dialect.get_table_names(db_session.connection())  # type: ignore[union-attr]
    assert "citations" not in table_names


def test_formatter_separate_from_assembler():
    assert CitationFormatter is not CitationAssembler


@pytest.mark.integration
def test_legal_object_effective_from_rendered_when_present(db_session):
    _, _, _, version = seed_source_version(db_session)
    version.version_label = ""
    version.effective_from = date(2020, 1, 1)
    version.effective_to = date(2020, 12, 31)
    db_session.flush()

    candidate = persist_candidate(
        db_session,
        make_candidate(source_version_id=str(version.id)),
    )
    set_version_effective_dates(
        db_session,
        candidate.legal_object_id,
        effective_from=date(2024, 7, 1),
        effective_to=date(2024, 12, 31),
    )
    legal_object = db_session.query(LegalObject).filter_by(
        legal_object_id=candidate.legal_object_id
    ).one()
    legal_object_version = db_session.query(LegalObjectVersion).filter_by(
        legal_object_id=candidate.legal_object_id
    ).one()

    result = CitationAssembler().assemble(
        db_session,
        legal_object,
        legal_object_version_id=legal_object_version.legal_object_version_id,
    )

    assert result.effective_from == date(2024, 7, 1)
    assert result.effective_to == date(2024, 12, 31)
    assert result.source_version_effective_from == date(2020, 1, 1)
    assert result.source_version_effective_to == date(2020, 12, 31)
    assert "Version effective 1 July 2024." in result.citation_text
    assert "Source version metadata: effective from 1 January 2020." in result.citation_text


@pytest.mark.integration
def test_no_source_version_fallback_when_legal_object_dates_missing(db_session):
    _, _, _, version = seed_source_version(db_session)
    version.version_label = ""
    version.effective_from = date(2023, 1, 1)
    version.effective_to = date(2023, 12, 31)
    db_session.flush()

    candidate = persist_candidate(
        db_session,
        make_candidate(source_version_id=str(version.id)),
    )
    legal_object = db_session.query(LegalObject).filter_by(
        legal_object_id=candidate.legal_object_id
    ).one()
    legal_object_version = db_session.query(LegalObjectVersion).filter_by(
        legal_object_id=candidate.legal_object_id
    ).one()
    assert legal_object_version.effective_from is None
    assert legal_object_version.effective_to is None

    result = CitationAssembler().assemble(
        db_session,
        legal_object,
        legal_object_version_id=legal_object_version.legal_object_version_id,
    )

    assert result.effective_from is None
    assert result.effective_to is None
    assert result.source_version_effective_from == date(2023, 1, 1)
    assert result.source_version_effective_to == date(2023, 12, 31)
    assert "Version effective 1 January 2023." not in result.citation_text
    assert "Source version metadata: effective from 1 January 2023." in result.citation_text


@pytest.mark.integration
def test_missing_legal_object_dates_remain_unknown_without_version_label(db_session):
    _, _, document, version = seed_source_version(db_session)
    version.version_label = ""
    version.effective_from = None
    version.effective_to = None
    document.official_reference = None
    db_session.flush()

    candidate = persist_candidate(
        db_session,
        make_candidate(source_version_id=str(version.id)),
    )
    legal_object = db_session.query(LegalObject).filter_by(
        legal_object_id=candidate.legal_object_id
    ).one()
    legal_object_version = db_session.query(LegalObjectVersion).filter_by(
        legal_object_id=candidate.legal_object_id
    ).one()

    result = CitationAssembler().assemble(
        db_session,
        legal_object,
        legal_object_version_id=legal_object_version.legal_object_version_id,
    )

    assert result.effective_from is None
    assert result.effective_to is None
    assert result.source_version_effective_from is None
    assert result.source_version_effective_to is None
    assert "Version effective" not in result.citation_text
    assert "Source version metadata:" not in result.citation_text
    assert result.citation_text.endswith("Statute.")


@pytest.mark.integration
def test_citation_hash_unaffected_by_temporal_metadata(db_session):
    _, _, _, version = seed_source_version(db_session)
    version.effective_from = date(2021, 6, 1)
    db_session.flush()

    candidate = persist_candidate(
        db_session,
        make_candidate(source_version_id=str(version.id)),
    )
    legal_object = db_session.query(LegalObject).filter_by(
        legal_object_id=candidate.legal_object_id
    ).one()
    legal_object_version = db_session.query(LegalObjectVersion).filter_by(
        legal_object_id=candidate.legal_object_id
    ).one()

    without_legal_dates = CitationAssembler().assemble(
        db_session,
        legal_object,
        legal_object_version_id=legal_object_version.legal_object_version_id,
    )
    set_version_effective_dates(
        db_session,
        candidate.legal_object_id,
        effective_from=date(2025, 3, 1),
        effective_to=date(2025, 9, 30),
    )
    with_legal_dates = CitationAssembler().assemble(
        db_session,
        legal_object,
        legal_object_version_id=legal_object_version.legal_object_version_id,
    )

    assert without_legal_dates.citation_hash == with_legal_dates.citation_hash
    assert without_legal_dates.citation_id == with_legal_dates.citation_id

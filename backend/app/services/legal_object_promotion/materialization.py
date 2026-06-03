"""Controlled materialization of parsed_structure into canonical legal_objects."""

import hashlib
from dataclasses import dataclass
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.orm import Session, joinedload

from app.models.legal_object_promotion_request import LegalObjectPromotionRequest
from app.models.parsed_structure import ParsedStructure
from app.models.parser_run import ParserRun
from app.models.source_version import SourceVersion
from app.services.legal_object_extraction.enums import (
    LegalObjectExtractionStatus,
    LegalObjectType,
)
from app.services.ingestion.enums import PipelineArtifactState
from app.services.ingestion.ingestion_state import (
    get_current_pipeline_state,
    update_ingestion_state,
)
from app.services.legal_object_persistence.repository import LegalObjectPersistenceRepository
from app.services.legal_object_persistence.status_enums import (
    LegalObjectStatus,
    LegalObjectVersionStatus,
)

LEGAL_OBJECT_ID_PREFIX = "ps-"
OBJECT_TYPE_PARSED_STRUCTURE = "parsed_structure"


@dataclass(frozen=True)
class ControlledMaterializationResult:
    legal_object_id: str
    legal_object_version_id: UUID
    created_legal_object: bool
    created_version: bool


def legal_object_id_for_parsed_structure(parsed_structure_id: UUID) -> str:
    """Deterministic legal object identity from canonical parsed_structure target."""
    return f"{LEGAL_OBJECT_ID_PREFIX}{parsed_structure_id}"


def _structure_units(parsed_structure: ParsedStructure) -> list[dict[str, Any]]:
    units = parsed_structure.structure_json.get("units")
    if not isinstance(units, list) or not units:
        raise ValueError("parsed_structure_missing")
    return units


def _map_unit_type(unit_type: str) -> str:
    try:
        return LegalObjectType(unit_type).value
    except ValueError:
        return LegalObjectType.UNKNOWN.value


def _build_structural_fields(
    parsed_structure: ParsedStructure,
    units: list[dict[str, Any]],
) -> tuple[str, str, str | None, str, int, int, str]:
    ordered = sorted(units, key=lambda u: (u.get("start_offset") or 0, u.get("end_offset") or 0))
    labels: list[str] = []
    text_parts: list[str] = []
    start_offset = end_offset = 0

    for unit in ordered:
        label = (unit.get("unit_label") or unit.get("unit_type") or "unit").strip()
        labels.append(label)
        raw = unit.get("raw_text") or ""
        if raw:
            text_parts.append(raw)
        start = int(unit.get("start_offset") or 0)
        end = int(unit.get("end_offset") or start)
        if not text_parts or start < start_offset:
            start_offset = start
        end_offset = max(end_offset, end)

    object_label = labels[0] if labels else str(parsed_structure.id)
    object_title = ordered[0].get("unit_title") if ordered else None
    canonical_path = " > ".join(labels[:8]) if labels else object_label
    raw_text = "\n".join(text_parts).strip() or object_label
    if end_offset < start_offset:
        end_offset = start_offset + max(len(raw_text), 1)

    return object_label, canonical_path, object_title, raw_text, start_offset, end_offset, _map_unit_type(
        ordered[0].get("unit_type") or OBJECT_TYPE_PARSED_STRUCTURE
    )


def _version_text_hash(parsed_structure: ParsedStructure, *, promotion_request_id: UUID) -> str:
    """Replay versions use a deterministic hash distinct from the default structure_hash."""
    payload = f"{parsed_structure.structure_hash}:{promotion_request_id}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _provenance_title(parsed_structure: ParsedStructure, parser_run_id: UUID) -> str:
    return (
        f"parsed_structure={parsed_structure.id};"
        f"parser_run={parser_run_id};"
        f"structure_hash={parsed_structure.structure_hash}"
    )


def materialize_legal_object_from_parsed_structure(
    db: Session,
    *,
    parsed_structure: ParsedStructure,
    promotion_request: LegalObjectPromotionRequest,
    repository: LegalObjectPersistenceRepository | None = None,
) -> ControlledMaterializationResult:
    """Create or append canonical legal memory from structural evidence only."""
    repo = repository or LegalObjectPersistenceRepository()

    source_version = (
        db.query(SourceVersion)
        .options(joinedload(SourceVersion.source_document))
        .filter(SourceVersion.id == parsed_structure.source_version_id)
        .first()
    )
    if source_version is None:
        raise ValueError("provenance_incomplete")

    parser_run = db.get(ParserRun, parsed_structure.parser_run_id)
    if parser_run is None:
        raise ValueError("parser_run_incomplete")

    document = source_version.source_document
    if document is None:
        raise ValueError("provenance_incomplete")

    units = _structure_units(parsed_structure)
    (
        object_label,
        canonical_path,
        object_title,
        raw_text,
        start_offset,
        end_offset,
        object_type,
    ) = _build_structural_fields(parsed_structure, units)

    legal_object_id = legal_object_id_for_parsed_structure(parsed_structure.id)
    if promotion_request.force_repromotion:
        text_hash = _version_text_hash(
            parsed_structure, promotion_request_id=promotion_request.id
        )
    else:
        text_hash = parsed_structure.structure_hash

    existing_object = repo.get_legal_object(db, legal_object_id)
    existing_version = repo.get_version_by_text_hash(
        db, legal_object_id=legal_object_id, text_hash=text_hash
    )
    if existing_version is not None:
        raise ValueError("duplicate_promotion")

    if existing_object is not None:
        if not promotion_request.force_repromotion:
            raise ValueError("duplicate_promotion")
        created_legal_object = False
    else:
        repo.create_legal_object(
            db,
            legal_object_id=legal_object_id,
            source_document_id=document.id,
            country_id=document.country_id,
            tax_type_id=document.tax_type_id,
            object_type=object_type,
            canonical_path=canonical_path,
            status=LegalObjectStatus.ACTIVE.value,
        )
        created_legal_object = True

    version_id = uuid4()
    version = repo.create_version(
        db,
        legal_object_version_id=version_id,
        legal_object_id=legal_object_id,
        source_version_id=parsed_structure.source_version_id,
        parent_legal_object_id=None,
        structural_unit_id=str(parsed_structure.id),
        object_label=object_label,
        object_title=_provenance_title(parsed_structure, parser_run.id),
        start_offset=start_offset,
        end_offset=end_offset,
        raw_text=raw_text,
        text_hash=text_hash,
        version_status=LegalObjectVersionStatus.ACTIVE.value,
        extraction_status=LegalObjectExtractionStatus.SUCCESS.value,
        effective_from=source_version.effective_from,
        effective_to=source_version.effective_to,
    )
    legal_object = repo.get_legal_object(db, legal_object_id)
    if legal_object is None:
        raise ValueError("unknown_failure")
    repo.set_current_version(db, legal_object, version.legal_object_version_id)

    current_pipeline = get_current_pipeline_state(
        db, source_version_id=parsed_structure.source_version_id
    )
    if current_pipeline == PipelineArtifactState.EXTRACTED.value:
        update_ingestion_state(
            db,
            source_version_id=parsed_structure.source_version_id,
            pipeline_state=PipelineArtifactState.PARSED.value,
            parser_run_id=parsed_structure.parser_run_id,
        )
        current_pipeline = PipelineArtifactState.PARSED.value
    if current_pipeline != PipelineArtifactState.LEGAL_OBJECTS_CREATED.value:
        update_ingestion_state(
            db,
            source_version_id=parsed_structure.source_version_id,
            pipeline_state=PipelineArtifactState.LEGAL_OBJECTS_CREATED.value,
            parser_run_id=parsed_structure.parser_run_id,
        )

    return ControlledMaterializationResult(
        legal_object_id=legal_object_id,
        legal_object_version_id=version.legal_object_version_id,
        created_legal_object=created_legal_object,
        created_version=True,
    )

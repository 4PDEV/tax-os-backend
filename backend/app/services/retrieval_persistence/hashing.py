"""Lifecycle request_hash for retrieval persistence (TASK-007C / RP-01)."""

import hashlib
import json
import uuid
from datetime import date
from uuid import UUID

SCOPE_ENVELOPE_KEYS = (
    "legal_object_id",
    "legal_object_type",
    "object_identifier",
    "source_document_id",
    "source_version_id",
)


def normalize_scope_envelope(scope_envelope: dict) -> dict:
    """Stable scope_envelope shape with explicit nulls and sorted keys."""
    normalized: dict = {}
    for key in SCOPE_ENVELOPE_KEYS:
        value = scope_envelope.get(key)
        if value is None:
            normalized[key] = None
        elif key == "source_version_id":
            normalized[key] = str(value)
        else:
            normalized[key] = value
    return normalized


def build_hash_payload(
    *,
    retrieval_mode: str,
    jurisdiction_code: str,
    scope_envelope: dict,
    include_canonical_text: bool,
    include_rendered_citation_text: bool,
    tax_type_code: str | None = None,
    as_of_date: date | None = None,
    legal_object_version_id: UUID | None = None,
    force_replay: bool = False,
    replay_nonce: str | None = None,
) -> dict:
    payload: dict = {
        "include_canonical_text": include_canonical_text,
        "include_rendered_citation_text": include_rendered_citation_text,
        "jurisdiction_code": jurisdiction_code,
        "retrieval_mode": retrieval_mode,
        "scope_envelope": normalize_scope_envelope(scope_envelope),
        "tax_type_code": tax_type_code,
    }
    if retrieval_mode == "AS_OF_DATE" and as_of_date is not None:
        payload["as_of_date"] = as_of_date.isoformat()
    if retrieval_mode == "EXACT_VERSION" and legal_object_version_id is not None:
        payload["legal_object_version_id"] = str(legal_object_version_id)
    if force_replay:
        payload["force_replay"] = True
        payload["replay_nonce"] = replay_nonce or str(uuid.uuid4())
    return payload


def canonical_json(payload: dict) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def compute_request_hash(
    *,
    retrieval_mode: str,
    jurisdiction_code: str,
    scope_envelope: dict,
    include_canonical_text: bool,
    include_rendered_citation_text: bool,
    tax_type_code: str | None = None,
    as_of_date: date | None = None,
    legal_object_version_id: UUID | None = None,
    force_replay: bool = False,
    replay_nonce: str | None = None,
) -> str:
    """Deterministic idempotency hash for default retrieval requests."""
    payload = build_hash_payload(
        retrieval_mode=retrieval_mode,
        jurisdiction_code=jurisdiction_code,
        scope_envelope=scope_envelope,
        include_canonical_text=include_canonical_text,
        include_rendered_citation_text=include_rendered_citation_text,
        tax_type_code=tax_type_code,
        as_of_date=as_of_date,
        legal_object_version_id=legal_object_version_id,
        force_replay=force_replay,
        replay_nonce=replay_nonce,
    )
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()

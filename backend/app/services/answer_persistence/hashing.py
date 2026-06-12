"""Lifecycle answer_request_hash for answer persistence (TASK-009B / DEC-011)."""

import hashlib
import json
import uuid
from uuid import UUID

CURRENT_CONTRACT_VERSION = "009B-v1"
DEFAULT_ASSEMBLY_CONTRACT_VERSION = "009A-v1"


def build_hash_payload(
    *,
    ranking_request_id: UUID,
    contract_version: str = CURRENT_CONTRACT_VERSION,
    assembly_contract_version: str = DEFAULT_ASSEMBLY_CONTRACT_VERSION,
    include_rendered_citation_text: bool = False,
    force_replay: bool = False,
    replay_nonce: str | None = None,
) -> dict:
    payload: dict = {
        "assembly_contract_version": assembly_contract_version,
        "contract_version": contract_version,
        "include_rendered_citation_text": include_rendered_citation_text,
        "ranking_request_id": str(ranking_request_id),
    }
    if force_replay:
        payload["force_replay"] = True
        payload["replay_nonce"] = replay_nonce or str(uuid.uuid4())
    return payload


def canonical_json(payload: dict) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def compute_answer_request_hash(
    *,
    ranking_request_id: UUID,
    contract_version: str = CURRENT_CONTRACT_VERSION,
    assembly_contract_version: str = DEFAULT_ASSEMBLY_CONTRACT_VERSION,
    include_rendered_citation_text: bool = False,
    force_replay: bool = False,
    replay_nonce: str | None = None,
) -> str:
    payload = build_hash_payload(
        ranking_request_id=ranking_request_id,
        contract_version=contract_version,
        assembly_contract_version=assembly_contract_version,
        include_rendered_citation_text=include_rendered_citation_text,
        force_replay=force_replay,
        replay_nonce=replay_nonce,
    )
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()

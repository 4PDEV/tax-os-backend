"""Lifecycle ranking_request_hash for ranking persistence (TASK-008C / RK-02)."""

import hashlib
import json
import uuid
from uuid import UUID

CURRENT_CONTRACT_VERSION = "008B-v2"


def build_hash_payload(
    *,
    retrieval_result_id: UUID,
    ranking_profile: str,
    contract_version: str = CURRENT_CONTRACT_VERSION,
    force_replay: bool = False,
    replay_nonce: str | None = None,
) -> dict:
    payload: dict = {
        "contract_version": contract_version,
        "ranking_profile": ranking_profile,
        "retrieval_result_id": str(retrieval_result_id),
    }
    if force_replay:
        payload["force_replay"] = True
        payload["replay_nonce"] = replay_nonce or str(uuid.uuid4())
    return payload


def canonical_json(payload: dict) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def compute_ranking_request_hash(
    *,
    retrieval_result_id: UUID,
    ranking_profile: str,
    contract_version: str = CURRENT_CONTRACT_VERSION,
    force_replay: bool = False,
    replay_nonce: str | None = None,
) -> str:
    payload = build_hash_payload(
        retrieval_result_id=retrieval_result_id,
        ranking_profile=ranking_profile,
        contract_version=contract_version,
        force_replay=force_replay,
        replay_nonce=replay_nonce,
    )
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()

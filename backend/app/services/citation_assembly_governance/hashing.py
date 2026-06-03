"""Lifecycle request_hash for citation assembly governance persistence.

request_hash (this module):
    Idempotency / append-only governance identity for ingestion-pipeline assembly requests.
    Default: derived from legal_object_version_id only.

TASK-004D rendered citation hash (app.services.citation.hash):
    Separate namespace for deterministic citation *content* after assembly execution.
    Must not be stored as request_hash or conflated with governance lifecycle hashes.
"""

import hashlib
import json
import uuid
from uuid import UUID


def compute_request_hash(
    *,
    legal_object_version_id: UUID,
    force_reassembly: bool = False,
) -> str:
    """Deterministic idempotency hash for default citation assembly requests.

    Default (force_reassembly=False): hash is based solely on legal_object_version_id.
    Force replay (force_reassembly=True): unique per request to preserve append-only audit rows.
    """
    if force_reassembly:
        payload = {
            "legal_object_version_id": str(legal_object_version_id),
            "force_reassembly": True,
            "replay_nonce": str(uuid.uuid4()),
        }
    else:
        payload = {"legal_object_version_id": str(legal_object_version_id)}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

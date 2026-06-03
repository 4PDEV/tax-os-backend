import hashlib
import json
import uuid
from uuid import UUID


def compute_promotion_hash(
    *,
    parsed_structure_id: UUID,
    force_repromotion: bool = False,
) -> str:
    """Deterministic idempotency hash for default promotion requests (canonical target only).

    Default (force_repromotion=False): hash is based solely on parsed_structure_id.
    Force replay (force_repromotion=True): unique per request to preserve append-only audit rows.
    """
    if force_repromotion:
        payload = {
            "parsed_structure_id": str(parsed_structure_id),
            "force_repromotion": True,
            "replay_nonce": str(uuid.uuid4()),
        }
    else:
        payload = {"parsed_structure_id": str(parsed_structure_id)}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

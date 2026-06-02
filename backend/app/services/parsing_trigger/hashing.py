import hashlib
import json
import uuid
from uuid import UUID


def compute_trigger_hash(
    *,
    extracted_text_id: UUID,
    force_reparse: bool = False,
) -> str:
    """Deterministic idempotency hash for default parsing triggers (canonical target only).

    Default (force_reparse=False): hash is based solely on extracted_text_id.
    Force replay (force_reparse=True): unique per request to preserve append-only audit rows.
    """
    if force_reparse:
        payload = {
            "extracted_text_id": str(extracted_text_id),
            "force_reparse": True,
            "replay_nonce": str(uuid.uuid4()),
        }
    else:
        payload = {"extracted_text_id": str(extracted_text_id)}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

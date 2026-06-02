import hashlib
import json
import uuid
from uuid import UUID


def compute_trigger_hash(
    *,
    source_version_id: UUID,
    force_reprocess: bool = False,
) -> str:
    """Deterministic idempotency hash for default triggers (canonical target only).

    Default (force_reprocess=False): hash is based solely on source_version_id.
    Force replay (force_reprocess=True): unique per request to preserve append-only audit rows.
    """
    if force_reprocess:
        payload = {
            "source_version_id": str(source_version_id),
            "force_reprocess": True,
            "replay_nonce": str(uuid.uuid4()),
        }
    else:
        payload = {"source_version_id": str(source_version_id)}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

import hashlib
import json
from uuid import UUID


def compute_trigger_hash(
    *,
    source_version_id: UUID,
    trigger_reason: str,
    requested_by_actor_type: str,
    rerun_allowed: bool,
    force_reprocess: bool,
) -> str:
    payload = {
        "source_version_id": str(source_version_id),
        "trigger_reason": trigger_reason.strip(),
        "requested_by_actor_type": requested_by_actor_type,
        "rerun_allowed": rerun_allowed,
        "force_reprocess": force_reprocess,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

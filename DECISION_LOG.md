# DECISION LOG

---

## DEC-001
LLMs must never answer tax or legal questions directly from model memory.

Status:
LOCKED

---

## DEC-002
All production answers must be source-referenced.

Status:
LOCKED

---

## DEC-003
Legal objects and source versions must never be silently overwritten.

Status:
LOCKED

---

## DEC-004
The platform must be effective-date-aware and version-aware.

Status:
LOCKED

---

## DEC-005
The system must surface ambiguity, conflicts, uncertainty, and risk rather than pretending certainty.

Status:
LOCKED

---

## DEC-006
Architecture authority remains centralized and governed.

Status:
LOCKED

---

## DEC-007
Development must occur through bounded tasks only.

Status:
LOCKED

---

## DEC-008
Agents may retrieve and structure information but may not autonomously publish production truth.

Status:
LOCKED

---

## DEC-009
The platform shall evolve progressively:
- country by country
- tax regime by tax regime
- module by module

Status:
LOCKED

---

## DEC-010
Ranking stores order only. Provenance lives once in `retrieval_evidence_references`. `ranked_evidence_references` are pure pointers (`retrieval_result_id`, `retrieval_evidence_reference_id`, `presentation_order_index`) — no copied provenance fields.

Authority: TASK-008C-REMEDIATION — [`RANKING_PERSISTENCE_REMEDIATION_008C-REMEDIATION.md`](RANKING_PERSISTENCE_REMEDIATION_008C-REMEDIATION.md); verified TASK-008C-PREAUTH-RECONCILIATION — [`TASKS/TASK-008C-PREAUTH-RECONCILIATION.md`](TASKS/TASK-008C-PREAUTH-RECONCILIATION.md)

Status:
LOCKED

---

## DEC-011 — Force Replay Hash Interpretation

For normal ranking requests (`force_replay = false`), `ranking_request_hash` remains:

```text
SHA-256(canonical_json({
  retrieval_result_id,
  ranking_profile,
  contract_version
}))
```

When `force_replay = true`, the persisted request-hash payload may include replay-specific entropy (e.g. `replay_nonce`) so an additional append-only lifecycle request can be recorded without colliding with the default de-duplication rule.

This interpretation:

- Exists only to allow an additional append-only lifecycle request row
- Does **not** change ranking determinism, ranking output, permutation validation, prerequisite validation, pure-pointer persistence, or provenance-once doctrine (DEC-010)
- Leaves the default non-replay de-duplication rule enforced by partial unique index `UNIQUE (ranking_request_hash) WHERE force_replay = false`

Authority: TASK-008C ranking persistence — Claude review finding F-10 (documentation closure); implementation in [`backend/app/services/ranking_persistence/hashing.py`](backend/app/services/ranking_persistence/hashing.py)

**TASK-008D and TASK-009A remain NOT AUTHORIZED.**

Status:
LOCKED

---

## DEC-012 — Ranking Execution Determinism and Boundary

Ranking execution applies **mechanical permutation over completed retrieval only**.

**Required:**

- Same `retrieval_result` + `ranking_profile` + `contract_version` ⇒ identical ordering (`presentation_order_index` assignment)
- Permutation integrity required — identical multiset of `retrieval_evidence_reference_id` values in and out
- `rank_count` equals retrieval evidence count (and persisted ranked row count)
- Zero-evidence completed retrieval ⇒ `ranking_status=completed`, `rank_count=0`, no error (`evidence_set_empty` prohibited)
- Pure-pointer persistence remains mandatory (DEC-010)
- Force replay behaviour governed by DEC-011
- Single-worker only (OD-021)

**Prohibited:**

- Retrieval re-selection
- AI ranking
- Semantic / vector ranking
- Answer generation
- Legal conclusions
- Citation synthesis

Authority: TASK-008D-PREAUTH — [`RANKING_EXECUTION_CONTRACT.md`](RANKING_EXECUTION_CONTRACT.md); [`TASKS/TASK-008D-RANKING-EXECUTION.md`](TASKS/TASK-008D-RANKING-EXECUTION.md)

**TASK-008D implementation and TASK-009A remain NOT AUTHORIZED.**

Status:
LOCKED

---

## DEC-013 — Answer Assembly Boundary and Provenance Read Model

Answer assembly constructs a **source-referenced answer package** from **completed ranking output only**.

**Required:**

- Consume terminal `ranking_status=completed` lifecycle and ranked evidence from the **accepted** `ranking_result` for the same `ranking_request_id` (RL-O-01)
- Load retrieval provenance **read-only** via `ranked_evidence_reference` → `retrieval_evidence_reference` joins (DEC-010)
- Preserve ranked evidence multiset and `presentation_order_index` order (E-01–E-07)
- Surface ambiguity and uncertainty explicitly (DEC-005) — no silent certainty
- Use answer-layer canonical error vocabulary — distinct from ranking errors
- Single-worker carry-forward (OD-021) until explicit concurrency governance

**Prohibited:**

- Retrieval execution or evidence re-selection
- Ranking execution or reordering
- Evidence invention, silent omission, or retrieval bypass
- Provenance duplication on answer-owned persistence
- Citation creation or canonical citation mutation
- Legal conclusions, applicability determination, or tax advice fields
- AI / semantic / vector ranking or unconstrained LLM answer generation (DEC-001)
- Answer runtime implementation without explicit authorization following 009A-PREAUTH acceptance

Authority: TASK-009A-PREAUTH — [`ANSWER_ASSEMBLY_CONTRACT.md`](ANSWER_ASSEMBLY_CONTRACT.md); [`TASKS/TASK-009A-ANSWER-ASSEMBLY.md`](TASKS/TASK-009A-ANSWER-ASSEMBLY.md)

**TASK-009A implementation remains NOT AUTHORIZED.**

Status:
LOCKED

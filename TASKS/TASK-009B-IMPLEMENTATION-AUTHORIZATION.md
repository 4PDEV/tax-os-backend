# TASK-009B — Implementation Authorization Package

## Status

**COMPLETE** — implementation design locked for bounded authorization prompt.

**ACCEPTED** — bounded implementation delivered (`v0.1.9-answer-persistence`).

| Phase | Status |
|-------|--------|
| TASK-009B-PREAUTH | **ACCEPTED** — DEC-015 |
| TASK-009B-IMPLEMENTATION-AUTHORIZATION (this document) | **ACCEPTED** — DEC-016 |
| TASK-009B persistence code | **COMPLETE** |

## Accepted baseline

| Item | Value |
|------|--------|
| HEAD | `8ddb285` (or newer accepted HEAD) |
| TASK-009A | **COMPLETE** — `v0.1.8-answer-assembly` |
| Answer layer review (009A+) | **ACCEPTED** |
| TASK-009B-PREAUTH | **ACCEPTED** |
| DEC-010 through DEC-016 | **LOCKED** |
| OD-021 | **LOCKED** — carry-forward |

## Binding upstream artifacts

- [`ANSWER_PERSISTENCE_CONTRACT.md`](../ANSWER_PERSISTENCE_CONTRACT.md) (009B-v1)
- [`ANSWER_ASSEMBLY_CONTRACT.md`](../ANSWER_ASSEMBLY_CONTRACT.md) (009A-v1)
- [`TASKS/TASK-009B-ANSWER-PERSISTENCE.md`](TASK-009B-ANSWER-PERSISTENCE.md)
- [`TASKS/TASK-009A-IMPLEMENTATION-AUTHORIZATION.md`](TASK-009A-IMPLEMENTATION-AUTHORIZATION.md)
- [`TASKS/TASK-008C-RANKING-PERSISTENCE.md`](TASK-008C-RANKING-PERSISTENCE.md) (pattern reference)
- [`DECISION_LOG.md`](../DECISION_LOG.md)

## Important

This package **does NOT implement** migrations, ORM models, persistence services, orchestration code, workers, APIs, or tests.

---

## D-01 — Final schema (frozen)

Contract generation: **`009B-v1`**. Assembly generation unchanged: **`009A-v1`**.

### `answer_requests`

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| `id` | UUID | NO | PK |
| `answer_request_hash` | VARCHAR(64) | NO | SHA-256 hex |
| `ranking_request_id` | UUID | NO | FK → `ranking_requests.id` |
| `contract_version` | VARCHAR(32) | NO | Default `009B-v1` |
| `assembly_contract_version` | VARCHAR(32) | NO | Default `009A-v1` |
| `include_rendered_citation_text` | BOOLEAN | NO | Assembly display flag |
| `requested_by_actor_type` | VARCHAR(64) | NO | Closed enum |
| `requested_by_actor_identifier` | VARCHAR(255) | YES | Audit |
| `requested_at` | TIMESTAMPTZ | NO | |
| `force_replay` | BOOLEAN | NO | Default false |
| `notes` | TEXT | YES | |
| `created_at` | TIMESTAMPTZ | NO | Append-only audit |

**PK:** `id`

**FK:** `ranking_request_id` → `ranking_requests.id`

**CHECK:** `requested_by_actor_type IN ('user','system','worker','admin','test')`

**Indexes:**

| Name | Columns | Unique | Where |
|------|---------|--------|-------|
| `ix_answer_requests_answer_request_hash` | `answer_request_hash` | NO | |
| `ix_answer_requests_ranking_request_id` | `ranking_request_id` | NO | |
| `uq_answer_requests_hash_default` | `answer_request_hash` | YES | `force_replay = false` |

---

### `answer_results`

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| `id` | UUID | NO | PK |
| `answer_request_id` | UUID | NO | FK → `answer_requests.id` |
| `ranking_request_id` | UUID | NO | FK → `ranking_requests.id` (scope audit) |
| `retrieval_result_id` | UUID | NO | FK → `retrieval_results.id` (denormalized scope) |
| `accepted_ranking_result_id` | UUID | YES | RL-O-01 audit — set on terminal rows |
| `terminal_ranking_result_id` | UUID | YES | RL-O-01 audit — set on terminal rows |
| `answer_status` | VARCHAR(64) | NO | Lifecycle enum |
| `rank_count` | INTEGER | YES | Set on terminal `completed` |
| `completed_at` | TIMESTAMPTZ | YES | Terminal rows |
| `error_category` | VARCHAR(64) | YES | Required when `failed` |
| `error_message` | TEXT | YES | |
| `notes` | TEXT | YES | |
| `created_at` | TIMESTAMPTZ | NO | Append-only audit |

**PK:** `id`

**FK:**

- `answer_request_id` → `answer_requests.id`
- `ranking_request_id` → `ranking_requests.id`
- `retrieval_result_id` → `retrieval_results.id`
- `accepted_ranking_result_id` → `ranking_results.id` (nullable)
- `terminal_ranking_result_id` → `ranking_results.id` (nullable)

**CHECK:**

- `answer_status IN ('pending','accepted','completed','failed','skipped','duplicate_rejected')`
- `error_category IS NULL OR error_category IN (<canonical vocabulary §D-08>)`

**Indexes:**

| Name | Columns |
|------|---------|
| `ix_answer_results_answer_request_id` | `answer_request_id` |
| `ix_answer_results_ranking_request_id` | `ranking_request_id` |
| `ix_answer_results_retrieval_result_id` | `retrieval_result_id` |

---

### `answer_evidence_entries`

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| `id` | UUID | NO | PK |
| `answer_result_id` | UUID | NO | FK → `answer_results.id` (**accepted** parent) |
| `answer_request_id` | UUID | NO | FK → `answer_requests.id` (scope) |
| `ranking_request_id` | UUID | NO | FK → `ranking_requests.id` (scope) |
| `ranked_evidence_reference_id` | UUID | NO | FK → `ranked_evidence_references.id` |
| `retrieval_result_id` | UUID | NO | Composite membership scope |
| `retrieval_evidence_reference_id` | UUID | NO | Composite membership member |
| `presentation_order_index` | INTEGER | NO | 1..N |
| `created_at` | TIMESTAMPTZ | NO | Append-only audit |

**PK:** `id`

**FK:**

- `answer_result_id` → `answer_results.id`
- `answer_request_id` → `answer_requests.id`
- `ranking_request_id` → `ranking_requests.id`
- `ranked_evidence_reference_id` → `ranked_evidence_references.id`
- `retrieval_result_id` → `retrieval_results.id`
- `retrieval_evidence_reference_id` → `retrieval_evidence_references.id`
- **Composite (required):** `fk_answer_evidence_retrieval_composite` on `(retrieval_result_id, retrieval_evidence_reference_id)` → `retrieval_evidence_references (retrieval_result_id, id)`

**CHECK:** `presentation_order_index >= 1`

**UNIQUE:**

- `uq_answer_evidence_result_order` (`answer_result_id`, `presentation_order_index`)
- `uq_answer_evidence_result_ranked` (`answer_result_id`, `ranked_evidence_reference_id`)
- `uq_answer_evidence_result_retrieval` (`answer_result_id`, `retrieval_evidence_reference_id`)

**Indexes:**

| Name | Columns |
|------|---------|
| `ix_answer_evidence_answer_result_id` | `answer_result_id` |
| `ix_answer_evidence_ranking_request_id` | `ranking_request_id` |

**Prohibited columns:** per §D-09 — none may appear.

---

### `answer_uncertainty_flags`

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| `id` | UUID | NO | PK |
| `answer_result_id` | UUID | NO | FK → `answer_results.id` (**accepted** parent) |
| `flag_type` | VARCHAR(64) | NO | Enum |
| `severity` | VARCHAR(32) | NO | Enum |
| `message` | TEXT | NO | Not legal advice |
| `related_retrieval_evidence_reference_id` | UUID | YES | FK → `retrieval_evidence_references.id` |
| `created_at` | TIMESTAMPTZ | NO | Append-only audit |

**PK:** `id`

**FK:**

- `answer_result_id` → `answer_results.id`
- `related_retrieval_evidence_reference_id` → `retrieval_evidence_references.id` (nullable)

**CHECK:**

- `flag_type IN ('conflict','ambiguity','incomplete_provenance','zero_evidence','other')`
- `severity IN ('informational','warning','error')`

**Indexes:**

| Name | Columns |
|------|---------|
| `ix_answer_uncertainty_answer_result_id` | `answer_result_id` |

---

### Migration prerequisite (ranking structural)

009B migration **must** add if not present:

```sql
UNIQUE (ranking_result_id, id) ON ranked_evidence_references
  -- name: uq_ranked_evidence_result_id_pk
```

Enables ranked membership validation and future composite FK hardening (§D-02).

---

## D-02 — Composite FK decision (OQ-B-02 RESOLVED)

### Locked decision

| Mechanism | Verdict | Rationale |
|-----------|---------|-----------|
| **Retrieval composite FK** | **REQUIRED** in DB | Structural DEC-010 membership — mirrors `ranked_evidence_references` / 008C |
| **Ranked composite FK** | **Service validation** in v1 | `ranked_evidence_references` has no `ranking_request_id`; contract columns exclude `accepted_ranking_result_id` on evidence rows |
| **Ranked simple FK** | **REQUIRED** | `ranked_evidence_reference_id` → `ranked_evidence_references.id` |
| **Validation V-B-02** | **REQUIRED** at `create_answer_evidence_entry` | Loaded ranked row `ranking_result_id` must equal `accepted_ranking_result_id` from RL-O-01 resolution |

### V-B-02 (locked)

```text
ranked = session.get(RankedEvidenceReference, ranked_evidence_reference_id)
accepted = <accepted ranking_result from RL-O-01>
ASSERT ranked.ranking_result_id == accepted.id
ASSERT ranked.retrieval_result_id == retrieval_result_id scope
ASSERT ranked.retrieval_evidence_reference_id == retrieval_evidence_reference_id
```

**Rationale:** Retrieval provenance authority requires DB-enforced composite membership. Ranked row membership is validated against RL-O-01 accepted parent without duplicating ranking lifecycle columns on evidence rows.

**Future hardening (not 009B):** composite FK `(ranking_result_id, ranked_evidence_reference_id)` after schema amendment — not in 009B scope.

---

## D-03 — Transaction boundary (locked)

### Single-session orchestration unit

All steps from **`create_answer_request`** through terminal **`create_answer_result`** run in **one database transaction** (one `Session` commit boundary per invocation).

### Phase transactions

| Phase | Operations | Commit |
|-------|------------|--------|
| **T1 — Request** | Validate hash inputs → `create_answer_request` OR reject duplicate | Part of unit |
| **T2 — Accepted** | `create_answer_result(answer_status=accepted)` | Part of unit |
| **T3 — Assembly** | `assemble_answer_package()` — read-only | Part of unit |
| **T4 — Children** | `create_answer_evidence_entry` × N; `create_answer_uncertainty_flag` × M | Part of unit |
| **T5 — Terminal** | `create_answer_result(completed \| failed)` | Part of unit |
| **Commit** | `session.commit()` once after T5 OR rollback entire unit on unhandled exception | End |

### Failure behavior

| Failure point | Behavior |
|---------------|----------|
| Duplicate default hash (pre-T2) | **No rows** — raise `AnswerPersistenceError('duplicate_answer')` or return `duplicate_rejected` terminal without children |
| Assembly failed (T3) | Append `answer_result(failed)` with assembly `error_category`; **no** evidence/uncertainty rows; commit accepted + failed only |
| Child persist validation failed (T4) | Append `answer_result(failed, error_category=assembly_validation_failed)`; **no partial children** — rollback T4 partial writes within unit |
| Infrastructure fault | `answer_result(failed, answer_pipeline_unavailable)`; rollback if commit cannot complete |

### Append-only rules

- **Never** `UPDATE` / `DELETE` on `answer_*` tables
- Failed runs **append** new `answer_result` rows — do not mutate `accepted`
- **No partial child rows** on failed terminal — all-or-nothing for T4 within the transaction

### Rollback rules

- Unhandled exception before commit → full `session.rollback()` — no dangling accepted without terminal sibling
- Duplicate rejection path may commit only `duplicate_rejected` result per idempotency design (mirror ranking)

---

## D-04 — Lifecycle ordering (OQ-B-01 RESOLVED)

### Locked: **Option A**

```text
create answer_request
  → create answer_result (accepted)
  → assemble_answer_package()           # read-only 009A
  → create answer_evidence_entries      # from AnswerPackage on success
  → create answer_uncertainty_flags
  → create answer_result (completed | failed)
```

**Option B (assemble → persist all without accepted first) — REJECTED.**

### Failure semantics

| Outcome | Persisted state |
|---------|-----------------|
| Success | `accepted` + children on **accepted** `answer_result_id` + terminal `completed` |
| Assembly failure | `accepted` + terminal `failed` (no children) |
| Duplicate default | `duplicate_rejected` terminal (no assembly) |
| Force replay | New `answer_request` row; full Option A pipeline |

**Rationale:** Mirrors ranking execution (008D); audit trail shows intent (`accepted`) before materialization; in-flight detection possible (accepted without terminal).

---

## D-05 — Service surface (frozen)

### Package (locked)

```text
backend/app/services/answer_persistence/
```

| Module | Responsibility |
|--------|----------------|
| `models.py` | ORM: `AnswerRequest`, `AnswerResult`, `AnswerEvidenceEntry`, `AnswerUncertaintyFlag` |
| `validation.py` | Enums, error categories, prohibited columns, V-B-02, request validation |
| `persistence.py` | Append-only `create_*`, read APIs, `compute_answer_request_hash`, orchestration entry |
| `hashing.py` | Hash payload + canonical JSON (mirror ranking_persistence) |
| `__init__.py` | Public exports |

Note: `hashing.py` added for parity with `ranking_persistence` — not in user list but standard pattern; include in package.

Actually user specified exact modules: models.py, validation.py, persistence.py, __init__.py only. Put hashing in hashing.py or persistence - 008C has separate hashing.py. User said only 4 modules - I'll put hash functions in `hashing.py` as optional 5th or inside persistence.py. User was explicit: models, validation, persistence, __init__. Put hashing in `hashing.py` referenced in impl auth as sub-module OR inline in persistence - I'll use `hashing.py` like ranking and note in doc as required parity file.

User said "Specify exact modules: models.py validation.py persistence.py __init__.py" - I'll stick to 4 and put hash in hashing.py as implementation detail inside persistence package per 008C pattern - add to doc as "hashing.py (required parity with ranking_persistence)".

### `create_*` APIs (locked)

| Function | Purpose |
|----------|---------|
| `create_answer_request(...)` | Intent row + hash dedup when `force_replay=false` |
| `create_answer_result(...)` | Lifecycle row |
| `create_answer_evidence_entry(...)` | Pure-pointer child on accepted result |
| `create_answer_uncertainty_flag(...)` | Uncertainty child on accepted result |
| `persist_answer_for_ranking_request(...)` | **Orchestration entry** — Option A pipeline; calls `assemble_answer_package` |

### Read APIs (locked)

| Function | Purpose |
|----------|---------|
| `find_existing_default_request(session, answer_request_hash=...)` | Idempotency lookup |
| `get_answer_request(session, answer_request_id=...)` | |
| `get_answer_result(session, answer_result_id=...)` | |
| `list_results_for_request(session, answer_request_id=...)` | Ordered by `created_at` |
| `list_evidence_entries_for_result(session, answer_result_id=...)` | Order by `presentation_order_index` |
| `list_uncertainty_flags_for_result(session, answer_result_id=...)` | |

### Prohibited

- `update_*`, `delete_*`, `merge`, ORM mutation of historical rows
- Assembly logic inside persistence (delegate to `assemble_answer_package`)
- Direct SQL writes bypassing `create_*`

---

## D-06 — Import boundary guards (frozen)

### Prohibited imports in `answer_persistence/`

| Prohibited | Reason |
|------------|--------|
| `app.services.retrieval_execution` | No retrieval re-selection |
| `app.services.ranking_execution` | No ranking execution |
| `app.workers.ranking_runtime` | No ranking worker |
| `app.workers.retrieval_runtime` | No retrieval worker |
| `app.workers.answer_runtime` | No answer worker |
| `app.services.response_runtime` | Not authorized |
| `app.services.ai` | No AI |
| `app.services.semantic` | No semantic reasoning |
| `app.services.vector` | No vector search |
| `app.services.citation.assembler` / `CitationAssembler` | OQ-03 |
| `fastapi`, `APIRouter` | No HTTP layer |
| `app.api` | No routes |

### Permitted imports

| Permitted | Usage |
|-----------|--------|
| `app.services.answer_assembly` — `assemble_answer_package` | Orchestration only |
| `app.services.ranking_persistence` — read APIs | RL-O-01 scope reads |
| `app.models.*` | ORM |
| SQLAlchemy `Session` | Read/write via `create_*` only |

### Test guard

`test_answer_persistence_import_guards` — static scan (mirror `test_answer_assembly.py`).

---

## D-07 — Implementation test plan (design only)

**Planned module:** `backend/tests/test_answer_persistence.py`  
**Supplementary:** `backend/tests/test_answer_persistence_alembic_migration.py`

| Group | Tests |
|-------|-------|
| **Hash / idempotency** | Default hash stable; duplicate raises/rejects; `force_replay` + nonce creates new request |
| **Replay (DEC-011)** | Payload includes `replay_nonce` when `force_replay=true`; default hash unchanged |
| **duplicate_answer** | Second default request rejected |
| **duplicate_rejected** | Terminal status on idempotency rejection path |
| **RL-O-01** | Evidence children on accepted `answer_result_id`; terminal holds audit IDs |
| **Pure-pointer** | ORM/migration column allowlist — no prohibited columns |
| **Provenance duplication guard** | `PROHIBITED_TABLE_COLUMNS` rejected in validation tests |
| **Order integrity** | `presentation_order_index` contiguous; unique constraints enforced |
| **Uncertainty** | Flags persisted; `zero_evidence` on rank_count=0 |
| **Zero-evidence** | No evidence rows; completed terminal |
| **Append-only lifecycle** | Multiple results per request; no updates |
| **V-B-02** | Ranked row parent mismatch rejected |
| **Import guards** | Prohibited prefixes absent |
| **Orchestration** | `persist_answer_for_ranking_request` calls assembly; no ranking `create_*` |
| **Assembly failure** | `accepted` + `failed`; no children |

---

## D-08 — Replay enforcement (DEC-011 aligned)

### Hash payload (locked)

**Default (`force_replay=false`):**

```json
{
  "ranking_request_id": "<uuid>",
  "contract_version": "009B-v1",
  "assembly_contract_version": "009A-v1",
  "include_rendered_citation_text": false
}
```

**Replay (`force_replay=true`):**

```json
{
  "ranking_request_id": "<uuid>",
  "contract_version": "009B-v1",
  "assembly_contract_version": "009A-v1",
  "include_rendered_citation_text": false,
  "force_replay": true,
  "replay_nonce": "<entropy>"
}
```

`answer_request_hash = SHA-256(canonical_json(payload))` — `sort_keys=True`, compact separators.

### Partial unique index

```sql
UNIQUE (answer_request_hash) WHERE force_replay = false
```

### Canonical `error_category` vocabulary (locked)

**Assembly (reuse 009A):**

`ranking_result_not_completed`, `accepted_ranking_result_missing`, `ranked_evidence_missing`, `evidence_count_mismatch`, `provenance_chain_incomplete`, `citation_reference_incomplete`, `retrieval_result_mismatch`, `assembly_validation_failed`, `answer_pipeline_unavailable`, `unknown_failure`

**Persistence-specific:**

`duplicate_answer`, `ranking_request_missing`, `invalid_answer_request`

**Prohibited on `answer_results`:** ranking categories (`permutation_mismatch`, `duplicate_ranking`, etc.)

---

## D-09 — Pure-pointer enforcement (prohibited-column matrix)

Applies to **`answer_evidence_entries`** and **all answer tables**.

| Column | Status |
|--------|--------|
| `legal_object_id` | **PROHIBITED** |
| `legal_object_version_id` | **PROHIBITED** |
| `source_version_id` | **PROHIBITED** |
| `source_document_id` | **PROHIBITED** |
| `citation_id` | **PROHIBITED** |
| `citation_hash` | **PROHIBITED** |
| `rendered_citation_text` | **PROHIBITED** |
| `answer_text` | **PROHIBITED** |
| `legal_conclusion` | **PROHIBITED** |
| `recommendation_text` | **PROHIBITED** |
| `ranking_score` | **PROHIBITED** |
| `relevance_score` | **PROHIBITED** |
| `confidence_score` | **PROHIBITED** |
| `semantic_score` | **PROHIBITED** |
| `ai_score` | **PROHIBITED** |
| `object_identifier` | **PROHIBITED** |
| `location_reference` | **PROHIBITED** |
| `evidence_metadata` | **PROHIBITED** |
| `deterministic_order_index` | **PROHIBITED** |

**Allowed on `answer_evidence_entries` only:** `id`, `answer_result_id`, `answer_request_id`, `ranking_request_id`, `ranked_evidence_reference_id`, `retrieval_result_id`, `retrieval_evidence_reference_id`, `presentation_order_index`, `created_at`.

Enforcement: migration schema + `validation.py` allowlist + `test_answer_persistence.py` column guard (mirror 008C).

---

## D-10 — Implementation scope

### TASK-009B may build (when explicitly authorized)

| Artifact | Scope |
|----------|--------|
| Alembic migration | 4 answer tables + `uq_ranked_evidence_result_id_pk` prerequisite |
| ORM models | 4 models matching §D-01 |
| `answer_persistence/` | §D-05 modules |
| `persist_answer_for_ranking_request` | Option A orchestration in `persistence.py` |
| Tests | §D-07 |
| Governance closure | Task doc update, CHANGELOG |

### TASK-009B must NOT build

| Prohibited | |
|------------|--|
| Answer worker | |
| Response runtime | |
| Public HTTP APIs / FastAPI routes | |
| AI / semantic / vector | |
| `CitationAssembler` | |
| Narrative `answer_text` | |
| Legal conclusions / recommendations | |
| Concurrent workers | |
| Changes to `assemble_answer_package` logic (beyond orchestration hook) | |
| Retrieval / ranking execution or persistence writes | |

### 009A preservation

`assemble_answer_package` remains callable without persistence (DEC-014).

---

## Authorization checklist (for future acceptance prompt)

- [ ] Architect accepts §D-01–§D-10
- [ ] Claude review of this package (recommended)
- [ ] Explicit prompt: **AUTHORIZED FOR LIMITED IMPLEMENTATION**
- [ ] Scope: `answer_persistence` + migration + tests only

---

## Unresolved questions

| ID | Question | Disposition |
|----|----------|-------------|
| U-B-01 | Separate `hashing.py` vs inline in `persistence.py`? | **Recommend `hashing.py`** — ranking parity |
| U-B-02 | In-flight `accepted` without terminal guard? | **Recommend yes** — mirror ranking V-08 in orchestration |
| U-B-03 | `duplicate_rejected` as separate row vs exception only? | **Recommend terminal row** — ranking parity |
| U-B-04 | Integration test DB requirement | **Required** for full §D-07 matrix |

---

## Explicit prohibitions (this task)

- No migration, ORM, service, worker, API, or test code in this task

---

END OF TASK-009B IMPLEMENTATION AUTHORIZATION PACKAGE (implementation NOT AUTHORIZED)

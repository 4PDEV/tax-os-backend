# Answer Persistence Contract

## Purpose

Define governed boundaries for **append-only answer persistence** — recording answer assembly intent, lifecycle, pure-pointer evidence membership, and uncertainty flags without duplicating provenance or crossing layer boundaries.

This contract is **governance only** (TASK-009B-PREAUTH). It authorizes the answer persistence **design envelope** for downstream bounded implementation. It does **not** authorize migrations, ORM models, persistence services, answer execution changes, workers, APIs, response runtime, or narrative answer generation.

## Core principle

**Answer persistence records assembly lifecycle and pure-pointer evidence membership — it does not assemble, rank, retrieve, duplicate provenance, or conclude legal force.**

```text
answer_request (persisted intent + answer_request_hash)
  → answer_result (accepted)
  → [answer assembly — existing 009A service]
  → answer_evidence_entries (pure pointers)
  → answer_uncertainty_flags (lifecycle metadata)
  → answer_result (completed | failed)
```

Answer persistence is **not**:

- answer assembly execution (009A service)
- ranking or retrieval execution
- provenance duplication or authoritative copy store
- citation creation or `CitationAssembler` invocation
- narrative `answer_text` or legal conclusions
- response delivery or public API surface

## Mandatory doctrines

| Doctrine | Rule |
|----------|------|
| `ranking` ≠ answer | Persistence consumes `ranking_request_id` — no re-ranking |
| `answer` ≠ legal conclusion | No applicability or legal-force fields |
| **Provenance lives once** (DEC-010) | Evidence pins authoritative in `retrieval_evidence_references`; answer rows are pointers only |
| **Append-only** | No updates/deletes to historical answer rows |
| **RL-O-01 preserved** | Persist `accepted_ranking_result_id` + `terminal_ranking_result_id`; ranked rows loaded from accepted parent at assembly |
| **Replay semantics** (DEC-011 pattern) | Default hash de-duplication; `force_replay` + `replay_nonce` for additional lifecycle rows |
| **009A assembly unchanged** | Persistence wraps `assemble_answer_package` — does not embed assembly logic |
| **Ephemeral 009A preserved** (DEC-014) | `assemble_answer_package` remains callable without persistence |

Upstream contracts (binding, closed):

- [`ANSWER_ASSEMBLY_CONTRACT.md`](ANSWER_ASSEMBLY_CONTRACT.md) (009A-v1)
- [`TASKS/ANSWER-LAYER-REVIEW.md`](TASKS/ANSWER-LAYER-REVIEW.md)
- [`TASKS/TASK-009A-IMPLEMENTATION-AUTHORIZATION.md`](TASKS/TASK-009A-IMPLEMENTATION-AUTHORIZATION.md)
- [`RANKING_RUNTIME_CONTRACT.md`](RANKING_RUNTIME_CONTRACT.md) (008B-v2)
- [`DECISION_LOG.md`](DECISION_LOG.md) — DEC-010 through DEC-015

---

## 1. Persistence model (governance decision)

### Recommendation: **Option B — append-only answer persistence**

| Option | Verdict | Rationale |
|--------|---------|-----------|
| **A — ephemeral only** | **Closed at 009A** (DEC-014) | Proved RL-O-01 and assembly boundaries without schema risk |
| **B — append-only persistence** | **RECOMMENDED for 009B** | Audit trail, idempotent lifecycle, platform parity with ranking (008C before execution) |

**Option B does not replace ephemeral assembly.** `assemble_answer_package` remains the assembly authority; persistence records intent + outcome.

**009B persistence scope (when authorized):** storage only — `create_*` APIs, no assembly algorithms, no workers, no APIs.

---

## 2. Lifecycle model

### Tables (append-only)

| Table | Role |
|-------|------|
| `answer_requests` | Intent envelope + `answer_request_hash` + upstream pins |
| `answer_results` | Lifecycle metadata (`answer_status`, `rank_count`, errors, ranking result refs) |
| `answer_evidence_entries` | Pure-pointer membership rows (one per ranked evidence item) |
| `answer_uncertainty_flags` | Persisted uncertainty metadata (DEC-005 surfacing) |

No separate `answer_errors` table — terminal errors live on `answer_results` (mirror ranking).

### Lifecycle pipeline

```text
answer_request (persisted)
  → answer_result (accepted)
  → resolve RL-O-01 + assemble_answer_package()
  → answer_evidence_entries × N (pure pointers)
  → answer_uncertainty_flags × M
  → answer_result (completed | failed)
```

### `answer_status` values (locked)

| Status | Meaning |
|--------|---------|
| `pending` | Reserved — pre-acceptance |
| `accepted` | Assembly authorized to proceed |
| `completed` | Package materialized; `rank_count` set |
| `failed` | Terminal error; `error_category` required |
| `skipped` | Reserved — dry-run / no-op (future worker skeleton) |
| `duplicate_rejected` | Idempotency rejection |

### Status transitions (append-only)

```text
create answer_request
  → create answer_result(accepted)
  → [assembly]
  → create answer_result(completed | failed)
```

On failure after `accepted`: append new `answer_result` row with `failed` — **no in-place mutation** of prior rows.

**Child row attachment:** `answer_evidence_entries` and `answer_uncertainty_flags` attach to the **`accepted`** `answer_result` row (mirror ranking RL-O-01 / RL-O-01 answer pattern). Terminal `completed`/`failed` row is a separate lifecycle row.

---

## 3. Identity / idempotency (DEC-011 pattern)

### Contract generation

`contract_version`: **`009B-v1`** (persistence generation; assembly remains `009A-v1`)

### Default `answer_request_hash` (locked)

```text
answer_request_hash = SHA-256(canonical_json({
  ranking_request_id,
  contract_version,
  assembly_contract_version,
  include_rendered_citation_text
}))
```

| Field | Rationale |
|-------|-----------|
| `ranking_request_id` | Primary upstream identity — same ranking + same flags ⇒ same default request |
| `contract_version` | Persistence generation (`009B-v1`) |
| `assembly_contract_version` | Assembly schema generation (`009A-v1`) |
| `include_rendered_citation_text` | Affects assembled output (CitationFormatter gate) |

**Excluded from hash:** actor fields, timestamps, notes, `replay_nonce` (unless `force_replay=true`).

### Force replay (DEC-011 carry-forward)

When `force_replay = true`, hash payload **may** include:

```text
{
  ...default fields...,
  "force_replay": true,
  "replay_nonce": "<entropy>"
}
```

| Rule | Requirement |
|------|-------------|
| Purpose | Additional append-only lifecycle row only |
| Does not bypass | RL-O-01 validation, assembly rules, pure-pointer shape |
| Does not alter | Assembly output for same ranking + flags |
| De-duplication | Partial unique `UNIQUE (answer_request_hash) WHERE force_replay = false` |

### Idempotency outcomes

| Scenario | Behavior |
|----------|----------|
| First default request | Persist + assemble + complete (or fail canonically) |
| Repeat default hash | Reject — `duplicate_answer` / `duplicate_rejected`; no re-assembly |
| `force_replay=true` + new nonce | New `answer_requests` row; full validation + assembly allowed |

---

## 4. Upstream resolution authority (RL-O-01)

### Authoritative inputs on `answer_requests`

| Column | Requirement |
|--------|-------------|
| `ranking_request_id` | **Required** — FK to `ranking_requests.id` |
| `assembly_contract_version` | Default `009A-v1` |
| `contract_version` | Default `009B-v1` |
| `include_rendered_citation_text` | Boolean — assembly display flag |
| `force_replay` | Boolean |
| `requested_by_actor_type` | Closed enum (mirror ranking) |

### Resolution at assembly time (binding — unchanged from 009A)

```text
1. Validate ranking_request exists
2. Load terminal ranking_result (ranking_status = completed) — exactly one
3. Load accepted ranking_result — exactly one
4. Load ranked_evidence_references from accepted.id
5. Verify len(ranked_rows) == terminal.rank_count
6. assemble_answer_package(...)
```

### Denormalized audit references on `answer_results` (allowed)

| Column | Purpose |
|--------|---------|
| `accepted_ranking_result_id` | RL-O-01 audit pin |
| `terminal_ranking_result_id` | RL-O-01 audit pin |
| `retrieval_result_id` | Scope audit (from `ranking_requests`) |
| `rank_count` | Terminal count at completion |

These are **lifecycle reference IDs** — not provenance duplication (same as ephemeral `AnswerPackage` fields).

**Prohibited:** accepting bare `terminal_ranking_result_id` as sole input without `ranking_request_id` resolution path.

---

## 5. Provenance protection (critical — DEC-010)

### Doctrine: **pure-pointer answer evidence rows**

Provenance remains authoritative in `retrieval_evidence_references`. Answer persistence stores **membership pointers only**.

### `answer_evidence_entries` allowed columns (locked)

| Column | Purpose |
|--------|---------|
| `id` | Surrogate PK |
| `answer_result_id` | Lifecycle parent (`accepted` row) |
| `ranking_request_id` | Membership scope |
| `ranked_evidence_reference_id` | Pointer to ranked row |
| `retrieval_result_id` | Composite membership scope |
| `retrieval_evidence_reference_id` | Pointer to evidence row (composite FK member) |
| `presentation_order_index` | Answer display order (1..N) — copied from ranked row |
| `created_at` | Append-only audit |

### Prohibited on `answer_evidence_entries` (and all answer tables)

| Column class | Reason |
|--------------|--------|
| `legal_object_id`, `legal_object_version_id` | Provenance duplication |
| `source_version_id`, `source_document_id` | Provenance duplication |
| `citation_id`, `citation_hash` | Provenance duplication — resolve via joins |
| `object_identifier`, `location_reference`, `evidence_metadata` | Provenance duplication |
| `rendered_citation_text` | Display — not authoritative store |
| `answer_text`, `legal_conclusion`, `recommendation_text` | Not authorized |
| Score columns (`ranking_score`, `relevance_score`, etc.) | Not authorized |

### Composite FK (required)

```text
FK (retrieval_result_id, retrieval_evidence_reference_id)
  → retrieval_evidence_references (retrieval_result_id, id)
```

Optional structural FK:

```text
FK (ranking_request_id, ranked_evidence_reference_id)
  → ranked_evidence_references via ranking_result membership validation at write time
```

### Read model for consumers

```text
answer_evidence_entry
  → ranked_evidence_reference
  → retrieval_evidence_reference
  → legal_object_version / citation / source_version (read-only)
```

---

## 6. Citation persistence (governance decision)

### Recommendation: **neither `citation_id` nor `rendered_citation_text` on persisted answer rows**

| Storage | Verdict |
|---------|---------|
| `citation_id` on `answer_evidence_entries` | **PROHIBITED** — resolve via join chain |
| `citation_hash` on answer rows | **PROHIBITED** |
| `rendered_citation_text` persisted | **PROHIBITED** — display cache not authoritative |

**At read time:** consumers may invoke read-only `CitationFormatter` when `include_rendered_citation_text` was true on the originating `answer_request` — same OQ-03 rule as 009A.

**`CitationAssembler`:** **PROHIBITED** in persistence and assembly paths.

---

## 7. Uncertainty persistence

### Recommendation: **persist uncertainty flags as append-only child rows**

Table: `answer_uncertainty_flags`

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID | Surrogate PK |
| `answer_result_id` | UUID | FK — parent `accepted` result |
| `flag_type` | enum | `conflict`, `ambiguity`, `incomplete_provenance`, `zero_evidence`, `other` |
| `severity` | enum | `informational`, `warning`, `error` |
| `message` | text | Human-readable; not legal advice |
| `related_retrieval_evidence_reference_id` | UUID nullable | Optional per-flag pin |
| `created_at` | timestamptz | Append-only |

**Rules:**

- Append-only — no updates/deletes
- Flags copied from ephemeral `AnswerPackage.uncertainty_flags` at completion
- `zero_evidence` flag **required** when `rank_count=0` and `completed`
- `conflict` / `ambiguity` automation deferred (009A-v1 does not infer — flags manual/structural only)

---

## 8. Failure model

### Assembly failures (reuse 009A categories on `answer_results`)

Canonical assembly `error_category` values — **unchanged from** [`ANSWER_ASSEMBLY_CONTRACT.md`](ANSWER_ASSEMBLY_CONTRACT.md) §6:

| Category | Layer |
|----------|-------|
| `ranking_result_not_completed` | Assembly prerequisite |
| `accepted_ranking_result_missing` | RL-O-01 |
| `ranked_evidence_missing` | Assembly |
| `evidence_count_mismatch` | Assembly |
| `provenance_chain_incomplete` | Assembly |
| `citation_reference_incomplete` | Assembly (reserved) |
| `retrieval_result_mismatch` | Assembly |
| `assembly_validation_failed` | Assembly |
| `answer_pipeline_unavailable` | Infrastructure |
| `unknown_failure` | Unclassified |

### Persistence-specific categories (additions for 009B)

| Category | Meaning |
|----------|---------|
| `duplicate_answer` | Default `answer_request_hash` collision |
| `ranking_request_missing` | FK validation — no ranking_request row |
| `invalid_answer_request` | Request envelope validation failure |

**Prohibited:** reuse of ranking categories (`permutation_mismatch`, `duplicate_ranking`) or retrieval categories as answer persistence terminal categories without mapping.

### Persistence write failures

Map infrastructure faults to `answer_pipeline_unavailable` on terminal `answer_result`.

---

## 9. Worker boundary (future — not authorized)

| Item | Decision |
|------|----------|
| Answer worker required? | **Deferred** — not required for 009B persistence slice |
| Recommended future task | **U-02** or **TASK-009C** — answer worker skeleton |
| Pattern | Single-worker orchestration (OD-021); delegates to `assemble_answer_package` + `answer_persistence` `create_*` only |
| 009B scope | **Persistence service only** — no worker |

Worker **must not** embed assembly, ranking, or retrieval logic.

---

## 10. API / response runtime boundary

| Layer | Responsibility | 009B status |
|-------|----------------|-------------|
| Answer persistence (009B) | Append-only storage | **Pre-auth only** |
| Answer assembly (009A) | Ephemeral package build | **Complete** |
| Response runtime | Delivery, formatting, transport | **NOT AUTHORIZED** |
| Public APIs | HTTP routes | **NOT AUTHORIZED** |

**Rule:** `answer assembly` ≠ `response runtime`. Persistence stores lifecycle + pointers; response runtime (future) reads `completed` answer results — no assembly at API boundary.

---

## 11. Zero-evidence persistence

When upstream ranking completed with `rank_count=0`:

| Step | Behavior |
|------|----------|
| `answer_result` terminal | `answer_status=completed`, `rank_count=0` |
| `answer_evidence_entries` | **None** — zero rows |
| `answer_uncertainty_flags` | One row: `flag_type=zero_evidence`, `severity=informational` |
| Error | **None** — `evidence_set_empty` prohibited (legacy) |

---

## 12. Implementation readiness criteria (G-01–G-05)

For **TASK-009B-IMPL-AUTH** and subsequent implementation authorization:

| ID | Criterion | 009B-PREAUTH status |
|----|-----------|---------------------|
| G-01 | Answer layer review accepted | **MET** |
| G-02 | Answer persistence contract exists (this document) | **MET** |
| G-03 | DEC-015 locked | **MET** (this pre-auth) |
| G-04 | Claude / reviewer acceptance of 009B-PREAUTH | **PENDING** |
| G-05 | Implementation authorization package (009B-IMPL-AUTH) | **NOT STARTED** |

### Design gates (pre-implementation — 009B-IMPL-AUTH)

| ID | Criterion |
|----|-----------|
| D-01 | Pure-pointer `answer_evidence_entries` schema frozen |
| D-02 | `answer_request_hash` + DEC-011 replay documented |
| D-03 | RL-O-01 accepted-row attachment rule documented |
| D-04 | Persistence error vocabulary distinct from ranking |
| D-05 | `create_*` only service boundary; no assembly in persistence |
| D-06 | Import guards defined |
| D-07 | Integration test plan (idempotency, zero-evidence, pure-pointer guards) |
| D-08 | No citation/provenance duplication tests |

---

## 13. Explicit prohibitions

| Capability | Status |
|------------|--------|
| TASK-009B implementation | **NOT AUTHORIZED** |
| Migrations / ORM / services / tests | **NOT AUTHORIZED** |
| Answer worker | **NOT AUTHORIZED** |
| Response runtime / public APIs | **NOT AUTHORIZED** |
| Narrative `answer_text` | **NOT AUTHORIZED** |
| Legal conclusions / recommendations | **NOT AUTHORIZED** |
| AI answer generation | **NOT AUTHORIZED** |
| Semantic / vector reasoning | **NOT AUTHORIZED** |
| `CitationAssembler` | **NOT AUTHORIZED** |
| Citation creation / mutation | **NOT AUTHORIZED** |
| Retrieval / ranking execution in persistence | **NOT AUTHORIZED** |
| Concurrent answer workers | **NOT AUTHORIZED** (OD-021) |
| Provenance duplication on answer rows | **PROHIBITED** |
| Persisted `rendered_citation_text` | **PROHIBITED** |

---

## 14. What 009B implementation may build (when authorized)

| Allowed | Not allowed |
|---------|-------------|
| Alembic migration for four tables | Answer assembly logic changes beyond `create_*` orchestration hook |
| ORM models (request, result, evidence entry, uncertainty flag) | Worker, API, response runtime |
| `answer_persistence/` service — `create_*` only | `CitationAssembler`, AI, semantic/vector |
| Read APIs: `get_answer_result`, `list_*` | Provenance columns on evidence rows |
| Tests: pure-pointer guards, hash idempotency, RL-O-01 integration | Narrative `answer_text`, legal conclusions |

**009A `assemble_answer_package` remains the assembly authority.** 009B may add an orchestration wrapper that persists lifecycle then calls assembly — or assembly-first with persist-on-success — but must not duplicate RL-O-01 or E-01–E-07 logic outside the existing service.

---

## 15. Sequencing

```text
009A-PREAUTH → 009A-IMPL-AUTH → 009A assembly (complete)
  → 009A+ Answer layer review (accepted)
  → 009B-PREAUTH (this contract)
  → [Claude review]
  → 009B-IMPL-AUTH
  → 009B persistence implementation (NOT AUTHORIZED)
  → Answer layer review update (future)
  → Answer worker (NOT AUTHORIZED)
  → Response runtime (NOT AUTHORIZED)
```

---

END OF ANSWER PERSISTENCE CONTRACT (TASK-009B-PREAUTH — governance only)

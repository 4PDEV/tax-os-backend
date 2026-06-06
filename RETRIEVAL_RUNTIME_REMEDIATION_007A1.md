# Retrieval Runtime Remediation — TASK-007A1

## Purpose

Authoritative remediation specification for future **TASK-007B** retrieval runtime, addressing blocking findings from [`ARCHITECTURE_REVIEW_RETRIEVAL_RUNTIME_007A-PREAUTH.md`](ARCHITECTURE_REVIEW_RETRIEVAL_RUNTIME_007A-PREAUTH.md).

**This document modifies planned architecture only.** It does not implement retrieval, persistence tables, migrations, workers, APIs, ranking, answers, or AI search.

| Item | Status |
|------|--------|
| TASK-007A pre-auth review | **Complete** — APPROVED WITH REQUIRED REMEDIATION BEFORE 007B |
| TASK-007A1 remediation package | **Complete** — R-01 through R-06 addressed at governance level |
| TASK-007A1 acceptance review | **Pending** — required before TASK-007B authorization |
| TASK-007B implementation | **NOT AUTHORIZED** |
| Ranking / answers / AI retrieval | **NOT AUTHORIZED** |

---

## Remediation index

| Finding | Severity | Remediation section | Status |
|---------|----------|---------------------|--------|
| R-01 | HIGH | Implicit latest via `current_version_id` | **Addressed (§R-01)** |
| R-02 | HIGH | Missing `legal_object_version_id` on results | **Addressed (§R-02)** |
| R-03 | HIGH | Evidence envelope / `canonical_text` collapse | **Addressed (§R-03)** |
| R-04 | HIGH | No runtime persistence doctrine | **Addressed (§R-04)** |
| R-05 | HIGH | No governed citation reference path | **Addressed (§R-05)** |
| R-06 | MEDIUM | `retrieve_by_id()` non-deterministic `.first()` | **Addressed (§R-06)** |
| R-07 | MEDIUM | `source_retrieval_log` namespace | **Addressed (§Naming)** |
| R-08 | MEDIUM | Ordering vs ranking ambiguity | **Addressed (§Ranking boundary)** |
| R-09 | MEDIUM | 004A contract purpose drift | **Carry-forward** — amend in 007B contract task |
| OD-021 | INFO | Concurrent retrieval workers | **Addressed (§OD-021)** |

---

## R-01 — Temporal selection doctrine (no silent latest)

### Problem (004A baseline)

When `effective_on` is `None`, `apply_effective_date_filter` joins via `LegalObject.current_version_id` — **implicit latest-version selection** without explicit operator intent.

### Required doctrine (runtime)

Retrieval runtime must **not** silently select current/latest version.

Every runtime request must specify **one** of:

| Mode | Meaning | Required inputs |
|------|---------|-----------------|
| **`AS_OF_DATE`** | Versions effective on a date | `as_of_date` (required) |
| **`EXACT_VERSION`** | Pin one `legal_object_version_id` | `legal_object_version_id` (required) |
| **`LATEST_VERSION`** | Use operational current pointer | `retrieval_mode=LATEST_VERSION` (explicit only) |

### Rules

1. `effective_on=None` must **not** imply latest in runtime — **prohibited** as default.
2. `LATEST_VERSION` is allowed only when `retrieval_mode` is explicitly set — never silent fallback.
3. `AS_OF_DATE` is the **recommended default mode** for governed evidence retrieval.
4. Runtime wrapper around 004A must reject requests missing mode + required pins (007B implementation).

### Relationship to 004A

TASK-004A service behavior on `main` is **unchanged** by this package. Runtime contract adds a **governance envelope** above 004A that enforces explicit temporal selection.

---

## R-02 — Version-pinned evidence (required fields)

### Problem

`LegalObjectRetrievalResult` (004A) lacks `legal_object_version_id`. Evidence cannot be replayed or handed to citation provenance without version pin.

### Required doctrine

Every runtime retrieval evidence item must be **version-pinned**.

### Required reference fields (minimum)

| Field | Required | Purpose |
|-------|----------|---------|
| `legal_object_id` | Yes | Stable object identity |
| `legal_object_version_id` | Yes | Version pin — **mandatory** |
| `source_version_id` | Yes | Source lineage |

**Retrieval without `legal_object_version_id` is prohibited** in runtime output.

### 007B implementation note

Extend or wrap 004A results to populate `legal_object_version_id` from the joined `LegalObjectVersion` row. Do not infer version from `legal_object_id` alone.

---

## R-03 — Evidence references, not answer content

### Problem

004A returns `canonical_text` by default — encourages answer-like consumption at runtime boundary.

### Required doctrine

```text
retrieval result ≠ answer
retrieval result ≠ legal conclusion
```

Runtime returns **evidence references**, not synthesized legal content.

### Default runtime evidence reference (planned DTO)

| Field | Default | Notes |
|-------|---------|-------|
| `legal_object_id` | Included | |
| `legal_object_version_id` | Included | Version pin |
| `citation_id` | Included when citation exists | Primary evidence handle |
| `citation_hash` | Optional | Canonical citation identity |
| `source_version_id` | Included | Provenance |
| `source_document_id` | Included | Provenance |
| `location_reference` | Included when citation joined | Structural location |
| `object_identifier` | Included | Structural reference |
| `integrity_hash` / `text_hash` | Optional metadata | Audit only |
| `canonical_text` | **Excluded by default** | Not default retrieval output |
| `rendered_citation_text` | **Excluded by default** | Join from `citations` only when explicitly requested |

### Optional content gates (explicit opt-in only)

| Flag | Effect |
|------|--------|
| `include_canonical_text` | Attach legal-object body from version row — labeled evidence payload, not answer |
| `include_rendered_citation_text` | Attach stored citation text from `citations` entity — not re-rendered |

Default runtime path: **references + provenance only**.

---

## R-04 — Runtime persistence doctrine

### Problem

No governed identity or append-only lifecycle for retrieval orchestration.

### Required architecture (planned — TASK-007B)

Append-only tables mirroring citation governance (006Z) and promotion (006V) precedent.

### Table: `retrieval_requests` (planned name)

| Column | Type / constraint | Notes |
|--------|-------------------|-------|
| `id` | UUID PK | `retrieval_request_id` |
| `request_hash` | String(64) NOT NULL, indexed | Lifecycle identity — see §Persistence identity |
| `retrieval_mode` | String(64) NOT NULL | `AS_OF_DATE` \| `EXACT_VERSION` \| `LATEST_VERSION` |
| `as_of_date` | Date, nullable | Required when mode = `AS_OF_DATE` |
| `legal_object_version_id` | UUID, nullable | Required when mode = `EXACT_VERSION` |
| `jurisdiction_code` | String, NOT NULL | Scope envelope |
| `tax_type_code` | String, nullable | Scope envelope |
| `scope_filters` | JSONB, nullable | Structural filters (document, type, identifier) — normalized for hash |
| `requested_by_actor_type` | String(64) CHECK | `user\|system\|worker\|admin\|test` |
| `requested_by_actor_identifier` | String(255), nullable | |
| `requested_at` | Timestamptz NOT NULL | |
| `force_replay` | Boolean NOT NULL default false | Governance replay bypass |
| `notes` | Text, nullable | Audit |
| `created_at` | Timestamptz NOT NULL | Append-only |

**Indexes / constraints (planned):**

- Partial unique on normalized default identity WHERE `force_replay = false` (006Z pattern)
- Index on `request_hash`

### Table: `retrieval_results` (planned name)

| Column | Type / constraint | Notes |
|--------|-------------------|-------|
| `id` | UUID PK | `retrieval_result_id` |
| `retrieval_request_id` | UUID FK NOT NULL | |
| `retrieval_status` | String(64) NOT NULL | `pending\|accepted\|completed\|failed\|skipped\|duplicate_rejected` |
| `result_count` | Integer, nullable | Evidence reference count |
| `completed_at` | Timestamptz, nullable | |
| `error_category` | String(64), nullable | |
| `error_message` | Text, nullable | |
| `notes` | Text, nullable | |
| `created_at` | Timestamptz NOT NULL | Append-only |

### Evidence references storage

Evidence reference list stored in **child table** or **JSONB column** on result — references only:

- `legal_object_id`, `legal_object_version_id`, `citation_id`, `citation_hash`, `source_version_id`, provenance metadata

**Prohibited on result rows:**

- answer text
- legal conclusions
- applicability flags
- relevance scores
- `canonical_text` (unless separate auditable payload table with explicit opt-in flag on request)
- AI-generated content

### `request_hash` is lifecycle identity only

Not evidence identity. Not query text. See §Persistence identity.

---

## R-05 — Citation reference retrieval doctrine

### Problem

006AD `citations` entity exists; 004A queries legal objects only. Runtime cannot return citation evidence without governed lookup.

### Required doctrine

Retrieval evidence must **reference citations** where available. Legal-object references alone are **insufficient** for governed evidence sets intended for downstream answer assembly.

### Citation evidence lookup (planned — read-only)

| Lookup key | Source | Rules |
|------------|--------|-------|
| `citation_id` | `citations` table | Primary operator handle |
| `citation_hash` | `citations` table | Canonical identity |
| Filter join | `legal_object_version_id` + scope | Returns citation references for version pin |

**Prohibited:**

- Re-invoking `CitationAssembler` during retrieval
- Creating new citations during retrieval
- Inferring applicability from citation presence

### Required provenance chain (every citation reference)

```text
citation_id / citation_hash
  → legal_object_version_id
  → legal_object_id
  → source_version_id
  → source_document_id
```

Runtime must validate chain resolvability before emitting citation reference. Broken lineage → `failed` result or omit with explicit error metadata — never silent drop.

---

## R-06 — Deterministic ordering doctrine

### Problem

`retrieve_by_id()` uses `.first()` without `apply_deterministic_order` when multiple version rows match — non-reproducible selection.

### Required doctrine

All retrieval selection and ordering must be **explicit and deterministic**.

### Permitted ordering keys (examples)

| Key | Use |
|-----|-----|
| `effective_from` ASC/DESC | Temporal tie-break (004A precedent) |
| `structural_unit_id`, `object_label` | Structural ordering |
| `created_at` | Append-order tie-break |
| `legal_object_id` | Stable final tie-break |
| `citation_hash` | Citation list ordering |

Runtime must apply declared `ORDER BY` before any single-row selection (`.first()` / `LIMIT 1`).

### Prohibited

- Implicit database row order
- Relevance scores
- “Best match” or “top result” semantics without explicit deterministic rule

### 007B implementation note

Wrap 004A `retrieve_by_id()` with `apply_deterministic_order()` before `.first()`; add integration test for multi-version overlap.

---

## Ranking boundary

| Capability | Status |
|------------|--------|
| Relevance ranking | **NOT AUTHORIZED** |
| Confidence scores | **NOT AUTHORIZED** |
| Semantic similarity ordering | **NOT AUTHORIZED** |
| Deterministic sort | **Allowed** |

```text
ordering ≠ ranking
```

Deterministic ordering is a **stable tie-break** for reproducibility — not an opinion about legal relevance.

Examples of permitted sort keys: `effective_from`, `version_number` (if modeled), `citation_hash`, `object_identifier`, `created_at`.

Examples of prohibited sort keys: relevance score, confidence, BM25, embedding distance.

---

## Persistence identity

### `request_hash` formula (planned)

```text
request_hash = SHA-256(normalized_retrieval_envelope)
```

**Normalized envelope includes:**

- `retrieval_mode`
- `as_of_date` (when applicable)
- `legal_object_version_id` (when applicable)
- `jurisdiction_code`
- `tax_type_code`
- normalized scope filters (document, source_version, object_type, object_identifier)
- contract version / schema generation (if multiple envelope versions ever required)

**Excluded from default hash:**

- raw `query_text` (if ever stored — audit metadata only)
- actor fields
- timestamps
- `notes`

### `force_replay`

- Explicit governance bypass for append-only audit replay
- Requires actor + reason (mirror `force_reassembly` / `force_reprocess`)
- Must not bypass provenance or temporal validation — only idempotency at request insert

### Dual identity (governance vs evidence)

| Identity | Purpose |
|----------|---------|
| `request_hash` | Retrieval **lifecycle** — “has this request been recorded?” |
| `citation_hash` | Citation **canonical** identity — unchanged from 006AD |
| Evidence reference list | **Not** hashed as single blob for identity — audit artifact on result row |

---

## Naming doctrine (R-07 carry-forward)

| Namespace | Purpose |
|-----------|---------|
| `retrieval_requests` / `retrieval_results` | Legal evidence retrieval runtime (007B) |
| `source_retrieval_log` | Source ingestion / monitoring fetch logs — **unrelated** |
| `LegalObjectRetrievalService` (004A) | In-memory deterministic legal-object query — underlying engine |

Packages (planned): `backend/app/services/retrieval_runtime/` or `legal_evidence_retrieval/` — distinct from `backend/app/services/retrieval/` (004A).

---

## OD-021 — Concurrent retrieval workers

### Current operating mode

- **Single-worker** retrieval orchestration acceptable on `main`
- Concurrent retrieval workers **not authorized**

### Creation-time idempotency (007B scope)

- Partial unique index on default `request_hash` / envelope WHERE `force_replay = false`
- Service-level duplicate rejection (006Z pattern)

### Execution-time risk (out of initial 007B scope)

Under concurrent workers, read-check-then-act races may duplicate work despite DB constraints.

### Future mitigations (documentation only)

- PostgreSQL advisory lock keyed by `request_hash`
- Row-level lock on `retrieval_requests` / result rows
- Worker skip when terminal `completed` exists for default identity

No concurrency implementation in TASK-007A1 or initial 007B unless separately authorized.

---

## Planned TASK-007B architecture (authoritative — not implemented)

```text
retrieval_request (request_hash idempotency)
  → retrieval runtime (single-worker)
  → evidence retrieval
      → legal_object_version references (004A wrapper)
      → citation references (citations table read)
  → retrieval_result (lifecycle + evidence reference list)
```

### Output (evidence set)

- `citation_id` / `citation_hash` references
- `legal_object_version_id` pins
- provenance metadata (`source_version_id`, `source_document_id`, structural identifiers)

### Explicit prohibitions in 007B flow

- No answers
- No legal conclusions
- No recommendations
- No applicability inference
- No ranking / relevance scores
- No AI / LLM / semantic search
- No citation re-assembly
- No modification of 004A contract behavior without separate bounded task

### Authorization gate for TASK-007B

TASK-007B may be authorized only after:

1. TASK-007A accepted — **done**
2. TASK-007A1 remediation package accepted — **pending acceptance review**
3. Bounded TASK-007B implementation spec derived from this document
4. Explicit governance approval — separate gate

---

## Relationship to existing artifacts

| Document | Role |
|----------|------|
| [`ARCHITECTURE_REVIEW_RETRIEVAL_RUNTIME_007A-PREAUTH.md`](ARCHITECTURE_REVIEW_RETRIEVAL_RUNTIME_007A-PREAUTH.md) | Pre-auth review — source findings |
| [`backend/app/services/retrieval/LEGAL_OBJECT_RETRIEVAL_CONTRACT.md`](backend/app/services/retrieval/LEGAL_OBJECT_RETRIEVAL_CONTRACT.md) | 004A baseline — unchanged |
| [`CITATION_EXECUTION_REMEDIATION_006AC1.md`](CITATION_EXECUTION_REMEDIATION_006AC1.md) | Identity/persistence precedent |
| [`TEMPORAL_VERSIONING_ARCHITECTURE.md`](TEMPORAL_VERSIONING_ARCHITECTURE.md) | `as_of_date` doctrine |
| [`CLAUDE_REVIEW_CITATION_PIPELINE_006Y-006AD.md`](CLAUDE_REVIEW_CITATION_PIPELINE_006Y-006AD.md) | Upstream citation layer |

---

## Acceptance criteria (007A1)

- [x] R-01 temporal selection doctrine documented
- [x] R-02 version-pinned evidence documented
- [x] R-03 evidence reference envelope documented
- [x] R-04 persistence doctrine documented
- [x] R-05 citation reference doctrine documented
- [x] R-06 deterministic ordering documented
- [x] Ranking boundary documented
- [x] Persistence identity (`request_hash`) documented
- [x] OD-021 carry-forward documented
- [x] Planned 007B flow documented
- [x] No implementation introduced
- [x] TASK-007B remains NOT AUTHORIZED

---

END OF RETRIEVAL RUNTIME REMEDIATION 007A1

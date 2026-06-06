# Citation Execution Remediation — TASK-006AC1

## Purpose

Authoritative remediation specification for **TASK-006AD** controlled citation execution, addressing remaining findings from [`TASKS/TASK-006AC-CONTROLLED-CITATION-EXECUTION-PREAUTH-REVIEW.md`](TASKS/TASK-006AC-CONTROLLED-CITATION-EXECUTION-PREAUTH-REVIEW.md).

**This document modifies planned architecture only.** It does not implement execution, rendering, citation entity tables, migrations, workers, retrieval, ranking, or answers.

| Item | Status |
|------|--------|
| 006AC pre-auth review | **Complete** — APPROVED WITH REQUIRED REMEDIATION BEFORE 006AD |
| TASK-004E (AC-01) | **Closed** — temporal fallback removed |
| TASK-006AC1 remediation package | **Complete** — AC-02 / AC-03 addressed at governance level |
| TASK-006AC1 acceptance review | **Complete** — TASK-006AD authorized with conditions |
| TASK-006AD implementation | **Complete** — see TASK-006AD controlled citation execution |
| Retrieval / answers | **NOT AUTHORIZED** |

---

## Remediation index

| Finding | Severity | Remediation section | Status |
|---------|----------|---------------------|--------|
| AC-01 | HIGH | Temporal inference via `source_version` date fallback | **Closed (TASK-004E)** |
| AC-02 | HIGH | Citation identity must conform to 004D provenance tuple | **Addressed (§AC-02)** |
| AC-03 | MEDIUM | Future citation entity must enforce DB uniqueness on citation identity | **Addressed (§AC-03)** |
| OD-021 | MEDIUM | Concurrent execution race — carry-forward for 006AD worker | **Addressed (§OD-021)** |

---

## AC-02 — Canonical citation identity (004D provenance tuple)

### Canonical formula

Citation identity is derived from **provenance**, not from rendering:

```text
citation_hash = SHA-256(
  source_version_id |
  legal_object_id |
  legal_object_version_id |
  location_reference
)
```

This **exactly aligns** with TASK-004D / AMENDMENT-A doctrine and the implemented assembler in `backend/app/services/citation/hash.py`.

`citation_id` is a deterministic display handle derived from `citation_hash` (prefix `cit_` + truncated hex). It is **not** a separate identity namespace.

### What citation identity must NOT depend on

Citation identity must **not** depend on:

- rendered citation text (`citation_text`)
- formatting or display style
- whitespace normalization in rendered output
- metadata field ordering in DTOs
- presentation changes (formatter version, label casing, date display format)
- `assembled_at` or assembly timestamps
- `assembler_version`
- actor, `citation_reason`, `notes`
- governance `request_hash`
- retrieval scores, ranking, applicability flags, or legal interpretation

### Rendering vs identity separation

| Concern | Governed by | May evolve? |
|---------|-------------|-------------|
| Citation **identity** | 004D provenance tuple (`citation_hash`) | No — stable for a given legal memory location |
| Citation **rendering** | `CitationFormatter`, `CitationResult` presentation fields | Yes — presentation may change without changing identity |

Rendered citation output may evolve. Citation identity must remain stable.

`citation_hash` is derived from provenance. Not from rendering.

### Identity invariants

1. Same provenance tuple → same `citation_hash` and `citation_id`.
2. Same `legal_object_id` with different `legal_object_version_id` → different `citation_hash`.
3. Same `legal_object_version_id` with different `location_reference` → different `citation_hash`.
4. `force_reassembly` creates a new **governance execution event** — it must **not** create a new `citation_hash` for the same provenance tuple.

### Dual-hash doctrine (governance vs citation)

Two hash namespaces — **must not be conflated**:

| Hash | Purpose | Key material | Used for |
|------|---------|--------------|----------|
| **`request_hash`** | Governance lifecycle identity | Default: `sha256(legal_object_version_id)`; force replay uses distinct replay material | Idempotency on `citation_assembly_governance_requests` |
| **`citation_hash`** | Canonical citation content identity | 004D provenance tuple (above) | Citation entity lookup, execution idempotency, DB uniqueness |

`request_hash` answers: *"Has this governance request been recorded?"*

`citation_hash` answers: *"What is the canonical identity of this legal memory citation?"*

---

## AC-03 — Citation uniqueness doctrine (future entity)

### Database requirement

When the citation entity is implemented (TASK-006AD scope), persistence must enforce:

```text
UNIQUE(citation_hash)
```

or an equivalent canonical uniqueness constraint on the full 64-character hash.

Partial indexes, surrogate keys, or composite keys that do not guarantee one row per `citation_hash` are **not sufficient** substitutes.

### Service-layer requirement

Database uniqueness alone is necessary but not sufficient. The execution service must:

1. Compute `citation_hash` from provenance before insert.
2. Look up existing citation by `citation_hash` before creating a new row.
3. On duplicate `citation_hash`, return or reference the existing citation — not create a second entity.

Both **service-level lookup** and **database uniqueness** are required.

### Execution idempotency key

Citation execution idempotency keys on:

- **`citation_hash`** — canonical citation identity

Citation execution idempotency does **not** key on:

- `request_hash` — governance lifecycle only
- governance request `id` — append-only audit row identity
- `legal_object_version_id` alone — insufficient when multiple location references exist per version

### Force reassembly and uniqueness

`force_reassembly=true` on a governance request:

- **May** append new governance request/result rows (audit trail).
- **May** trigger a new assembly execution event.
- **Must not** produce a new `citation_hash` when provenance tuple is unchanged.
- **Must** upsert or return existing citation entity keyed by `citation_hash`.

Re-rendering may update `rendered_citation_text` and `assembled_at` on the citation entity. Identity remains `citation_hash`.

---

## Citation identity lifecycle

```text
legal_object_version
  → location_reference (from object_type + object_label)
  → citation_hash (004D provenance tuple)
  → citation entity (future — TASK-006AD)
```

The same legal memory location (same `source_version_id`, `legal_object_id`, `legal_object_version_id`, `location_reference`) must **always** resolve to the same `citation_hash` and `citation_id`.

Assembly is deterministic: given the same inputs, `CitationAssembler` produces the same hash regardless of when assembly runs.

---

## Planned citation entity shape (TASK-006AD — not implemented)

### Table: `citations` (planned name — subject to 006AD task spec)

| Column | Required | Notes |
|--------|----------|-------|
| `citation_id` | Yes | Derived from `citation_hash`; stable handle |
| `citation_hash` | Yes | **UNIQUE** — canonical identity |
| `legal_object_id` | Yes | Provenance pin |
| `legal_object_version_id` | Yes | Version pin |
| `source_version_id` | Yes | Source lineage |
| `location_reference` | Yes | Structural location |
| `rendered_citation_text` | Yes | Presentation output — not identity input |
| `assembled_at` | Yes | Last successful assembly timestamp |
| `created_at` | Yes | Entity row creation |

### Optional fields (provenance metadata)

May include non-identity assembly metadata, e.g.:

- `authority_type`
- `source_title`, `official_reference`
- `publication_date`
- `effective_from` / `effective_to` (legal-object applicability only — per TASK-004E)
- `source_version_effective_from` / `source_version_effective_to` (labeled metadata only)
- `assembler_version`

Optional metadata must **not** participate in `citation_hash`.

### Prohibited fields

The citation entity must **not** store:

- retrieval score
- ranking score
- answer text
- applicability flags (inferred or computed)
- legal interpretation or legal meaning
- `latest` / `current` flags
- inferred temporal or legal status
- AI-generated content

---

## Governance result boundary

`citation_assembly_governance_results` (implemented — TASK-006Z) remains **lifecycle-only**.

### Allowed on governance result

| Field | Role |
|-------|------|
| `citation_id` | Nullable pointer to citation entity after successful execution |
| `citation_status` | Lifecycle terminal state (`assembled`, `failed`, `skipped`, etc.) |
| `assembled_at` | Handoff timestamp |
| `error_category` / `error_message` | Failure metadata |
| `notes` | Audit |
| Denormalized pins (`legal_object_id`, `legal_object_version_id`) | Queryability — already implemented |

### Prohibited on governance result

Governance results must **not** store:

- `citation_hash`
- `rendered_citation_text` or any rendered payload
- citation DTO serialization
- retrieval metadata
- ranking metadata
- applicability inference

Citation **content** belongs to the citation entity only. Governance results record **whether** and **when** assembly succeeded and **which** `citation_id` was produced.

---

## OD-021 — Concurrent execution carry-forward

### Current operating mode

- **Single-worker** citation assembly orchestration is acceptable on `main`.
- Concurrent citation execution workers are **not authorized**.

Creation-time idempotency on governance requests is closed (006Z partial unique on `legal_object_version_id` WHERE `force_reassembly = false`).

### Future concurrent execution (006AD worker scope)

When concurrent citation workers are authorized, **database uniqueness on `citation_hash` alone is insufficient** for execution-time race safety.

Future worker implementation must add execution-time protection:

- PostgreSQL **advisory lock** keyed by `citation_hash`, **or**
- **row-level lock** on citation entity row keyed by `citation_hash`

Lock scope: citation entity insert/upsert path — not governance request insert alone.

Worker skip rule: if terminal `assembled` governance result exists for default request identity **and** citation entity exists for `citation_hash`, skip duplicate work.

Document only in 006AC1 — implement in TASK-006AD when authorized.

---

## Planned TASK-006AD architecture (authoritative — not implemented)

```text
legal_object_version
  → citation_assembly_governance_request (request_hash idempotency)
  → governance worker (controlled execution)
  → deterministic citation renderer (004D CitationAssembler — in-memory)
  → citation entity (UNIQUE citation_hash)
  → citation_assembly_governance_result (citation_id pointer, lifecycle only)
```

### Explicit prohibitions in 006AD flow

- No retrieval
- No ranking
- No answers
- No applicability inference
- No legal advice or legal meaning derivation
- No silent temporal inference (TASK-004E compliance required)

### Authorization gate for TASK-006AD

TASK-006AD authorization chain (complete):

1. TASK-004E accepted (AC-01 closed) — **done**
2. TASK-006AC1 remediation package accepted (AC-02 / AC-03 closed at spec level) — **done**
3. TASK-006AC1 acceptance review — **done** — TASK-006AD **authorized with conditions**
4. Bounded TASK-006AD implementation — **complete**

---

## Relationship to existing artifacts

| Document | Role |
|----------|------|
| [`TASKS/TASK-006AC-CONTROLLED-CITATION-EXECUTION-PREAUTH-REVIEW.md`](TASKS/TASK-006AC-CONTROLLED-CITATION-EXECUTION-PREAUTH-REVIEW.md) | Pre-auth review — source findings (AC-01–AC-07) |
| [`backend/app/services/citation/CITATION_ASSEMBLY_CONTRACT.md`](backend/app/services/citation/CITATION_ASSEMBLY_CONTRACT.md) | 004D assembler contract — hash formula |
| [`CITATION_ASSEMBLY_CONTRACT.md`](CITATION_ASSEMBLY_CONTRACT.md) | 006Y governance layer — request/result lifecycle |
| [`CITATION_PERSISTENCE_REMEDIATION_006ZA.md`](CITATION_PERSISTENCE_REMEDIATION_006ZA.md) | 006Z persistence — `request_hash` vs rendered hash |
| [`TASKS/TASK-004E-CITATION-TEMPORAL-COMPLIANCE-REMEDIATION.md`](TASKS/TASK-004E-CITATION-TEMPORAL-COMPLIANCE-REMEDIATION.md) | AC-01 closure |

---

## Acceptance criteria (006AC1)

- [x] AC-02 canonical citation identity documented (004D provenance tuple)
- [x] AC-03 uniqueness doctrine documented (`UNIQUE(citation_hash)` + service lookup)
- [x] Citation identity lifecycle documented
- [x] Future citation entity shape documented
- [x] Governance result boundary documented
- [x] OD-021 carry-forward documented (`citation_hash`-keyed execution locks)
- [x] Planned 006AD architecture documented
- [x] No implementation introduced
- [x] TASK-006AD authorized with conditions — implementation not yet started

---

END OF CITATION EXECUTION REMEDIATION 006AC1

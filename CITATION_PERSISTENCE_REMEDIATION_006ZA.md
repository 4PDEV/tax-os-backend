# Citation Persistence Remediation — TASK-006ZA

## Purpose

Authoritative remediation specification for planned TASK-006Z citation persistence, addressing findings from [`ARCHITECTURE_REVIEW_CITATION_PERSISTENCE_006Z-PREAUTH.md`](ARCHITECTURE_REVIEW_CITATION_PERSISTENCE_006Z-PREAUTH.md).

**This document modifies planned architecture only.** It does not implement persistence, migrations, workers, execution, retrieval, or answers.

| Item | Status |
|------|--------|
| 006Z pre-auth review | **Complete** — APPROVED WITH REQUIRED REMEDIATION |
| TASK-006ZA remediation package | **Complete** |
| TASK-006Z implementation | **NOT AUTHORIZED** — requires explicit remediation acceptance + authorization gate |

---

## Remediation index

| Finding | Severity | Remediation section | Status |
|---------|----------|---------------------|--------|
| Z-01 | HIGH | §Z-01 `legal_object_id` | Addressed |
| Z-02 | MEDIUM | §Z-02 `source_version_id` | Addressed |
| Z-03 | HIGH | §Z-03 namespace separation | Addressed |
| Z-04 | MEDIUM | §Z-04 result shape | Addressed |
| Z-05 | LOW | §Z-05 `assembled_at` | Addressed |
| Z-07 | INFORMATIONAL | §Z-07 dual-hash doctrine | Addressed |
| Z-14 | MEDIUM | §Z-14 OD-021 | Addressed |

---

## Z-01 — `legal_object_id` on request and result

### Planned request fields (required)

- `legal_object_id` — FK → `legal_objects.legal_object_id`, NOT NULL
- `legal_object_version_id` — FK → `legal_object_versions.legal_object_version_id`, NOT NULL

### Doctrine

`legal_object_version` must belong to `legal_object`. Citation assembly targets a **version pin** within a **stable object identity**.

### Planned validation (application layer, future 006Z)

Reject request when:

```text
legal_object_version.legal_object_id != request.legal_object_id
```

Error category: `invalid_request` (or dedicated `legal_object_version_mismatch` if taxonomy extended later).

### Planned result denormalization

- `legal_object_id` — NOT NULL on `citation_assembly_results`
- `legal_object_version_id` — NOT NULL on `citation_assembly_results`

Rationale: queryability, auditability, alignment with `legal_object_promotion_results` denormalizing `parsed_structure_id` and `legal_object_id`.

---

## Z-02 — `source_version_id` denormalization

### Planned request field (required)

- `source_version_id` — FK → `source_versions.id`, NOT NULL

### Purpose

- Lineage audit without multi-hop joins
- Operator review consistency with TASK-006V (`legal_object_promotion_requests.source_version_id`)
- Traceability: `source_version` → … → citation assembly request

### Planned validation (application layer, future 006Z)

Reject request when:

```text
legal_object_version.source_version_id != request.source_version_id
```

Error category: `provenance_incomplete` or `invalid_request`.

---

## Z-03 — Namespace separation from TASK-004D

### Mandatory rule

Planned persistence entities **must NOT** use:

- `CitationAssemblyRequest`
- `CitationAssemblyResult`

Those names are reserved for TASK-004D assembler DTOs in `backend/app/services/citation/models.py`.

### Planned governance naming

| Layer | Name |
|-------|------|
| SQL tables | `citation_assembly_requests`, `citation_assembly_results` (unchanged) |
| ORM / service models | `CitationAssemblyGovernanceRequest`, `CitationAssemblyGovernanceResult` |
| Recommended module | `app.services.citation_assembly_governance` or `app.services.ingestion_citation_assembly` |

### Complementarity (no ambiguity)

| Path | Role |
|------|------|
| TASK-004D | Deterministic **citation rendering** — `CitationAssembler`, `CitationResult` |
| TASK-006Y / 006Z | Ingestion **governance lifecycle** — append-only assembly requests/results |

Goal: no import ambiguity, no DTO ambiguity, no test ambiguity.

---

## Z-04 — Complete planned result shape

### Planned `citation_assembly_results` fields

| Field | Nullable | Notes |
|-------|----------|-------|
| `id` (result PK) | No | UUID — `citation_assembly_result_id` in docs |
| `citation_assembly_request_id` | No | FK → requests |
| `legal_object_id` | No | Denormalized (Z-01) |
| `legal_object_version_id` | No | Denormalized |
| `citation_status` | No | Enum CHECK per 006Y |
| `citation_id` | Yes | Null until execution/materialization exists |
| `assembled_at` | Yes | Terminal success timestamp (Z-05) |
| `error_category` | Yes | Per 006Y taxonomy |
| `error_message` | Yes | Operator detail |
| `notes` | Yes | Audit |
| `created_at` | No | Append-only row metadata (006V pattern) |

Rationale: direct audit queries by version/object; 006V alignment; no join required for common operator views.

**Not on result:** `request_hash` lives on request only (006V `promotion_hash` precedent).

---

## Z-05 — `assembled_at` (not `completed_at`)

Use **`assembled_at`** on results for terminal success handoff.

Do **not** use `completed_at` for 006Z — avoids drift from 006Y (`assembled` status) and promotion `promoted_at` naming parallel.

Reserve multi-phase timestamps (`queued_at`, `started_at`) for a future worker skeleton task if needed.

---

## Z-07 — Dual-hash doctrine

Two hash namespaces — **must not be conflated**.

### 1. Governance request hash (ingestion lifecycle)

| Property | Value |
|----------|--------|
| Field name (planned) | `request_hash` |
| Default (`force_reassembly=false`) | `sha256(legal_object_version_id)` |
| Force replay (`force_reassembly=true`) | Unique per replay request (e.g. version id + force flag + request id nonce) |
| Used for | Idempotency, duplicate rejection, append-only audit |
| Location | `citation_assembly_requests.request_hash` |

**Excluded from default hash:** actor, `citation_reason`, timestamps, `notes`, citation text.

### 2. Rendered citation hash (TASK-004D)

| Property | Value |
|----------|--------|
| Governed by | `backend/app/services/citation/CITATION_ASSEMBLY_CONTRACT.md` |
| Formula (004D) | `SHA-256(source_version_id \| legal_object_id \| legal_object_version_id \| location_reference)` |
| Used for | Deterministic citation **content** identity after assembly execution |
| Location | Future execution output / `CitationResult` — **not** 006Z request tables |

**These hashes are different.** 006Z persistence records governance state; 004D hashes rendered citation artifacts.

---

## Z-14 — OD-021 carry-forward

### Current operating constraint

- **Single-worker** citation assembly orchestration acceptable on `main`.
- Concurrent citation workers **not authorized**.

### Creation-time idempotency (006Z scope)

- Partial unique index: `legal_object_version_id` WHERE `force_reassembly = false`
- Mirrors 006P1 / 006R / 006V / 006X1

### Execution-time risk (out of 006Z scope)

Under concurrent workers, read-check-then-act races may duplicate work despite DB partial unique constraints at request insert time.

### Future mitigations (documentation only — implement in worker task)

- Row-level locking on assembly request/result rows
- PostgreSQL advisory locks keyed by `legal_object_version_id`
- Worker-level skip when terminal `assembled` exists for default identity

No concurrency implementation in TASK-006ZA or TASK-006Z persistence-only scope.

---

## Planned TASK-006Z persistence shape (authoritative after 006ZA)

### Table: `citation_assembly_requests`

| Column | Type / constraint |
|--------|-------------------|
| `id` | UUID PK |
| `legal_object_id` | String(64) FK → `legal_objects.legal_object_id`, NOT NULL |
| `legal_object_version_id` | UUID FK → `legal_object_versions.legal_object_version_id`, NOT NULL |
| `source_version_id` | UUID FK → `source_versions.id`, NOT NULL |
| `citation_reason` | Text, NOT NULL |
| `requested_by_actor_type` | String(64), CHECK `user|system|worker|admin|test` |
| `requested_by_actor_identifier` | String(255), nullable |
| `requested_at` | Timestamptz, NOT NULL |
| `force_reassembly` | Boolean, NOT NULL, default false |
| `request_hash` | String(64), NOT NULL, indexed |
| `notes` | Text, nullable |
| `created_at` | Timestamptz, NOT NULL |

**Indexes / constraints:**

- Partial unique: `legal_object_version_id` WHERE `force_reassembly = false`
- Index on `request_hash`
- Index on `legal_object_version_id`

### Table: `citation_assembly_results`

| Column | Type / constraint |
|--------|-------------------|
| `id` | UUID PK |
| `citation_assembly_request_id` | UUID FK → requests, NOT NULL |
| `legal_object_id` | String(64) FK, NOT NULL |
| `legal_object_version_id` | UUID FK, NOT NULL |
| `citation_status` | String(64), CHECK 006Y status enum |
| `citation_id` | String, nullable — no FK until citation entity table exists |
| `assembled_at` | Timestamptz, nullable |
| `error_category` | String(64), nullable, CHECK 006Y error enum |
| `error_message` | Text, nullable |
| `notes` | Text, nullable |
| `created_at` | Timestamptz, NOT NULL |

**Out of scope for 006Z tables:** citation text, authority interpretation, applicability flags, ranking scores, answer payloads, rendered 004D hash storage (execution phase).

### ORM naming (Z-03)

- `CitationAssemblyGovernanceRequest` → `citation_assembly_requests`
- `CitationAssemblyGovernanceResult` → `citation_assembly_results`

---

## Idempotency and replay (unchanged doctrine, clarified naming)

| Concept | Value |
|---------|--------|
| Default canonical identity | `legal_object_version_id` |
| Sole replay bypass | `force_reassembly=True` |
| Default request hash | `sha256(legal_object_version_id)` |
| DB guard | Partial unique on `legal_object_version_id` WHERE `force_reassembly = false` |

`citation_reason` and actor fields must **not** bypass idempotency.

---

## Authorization gate (TASK-006Z)

TASK-006Z remains **NOT AUTHORIZED** until:

1. This remediation package is **accepted** by governance (006ZA complete).
2. A separate explicit **AUTHORIZED FOR IMPLEMENTATION** instruction is issued for TASK-006Z.

006ZA does not substitute for step 2.

---

## References

- [ARCHITECTURE_REVIEW_CITATION_PERSISTENCE_006Z-PREAUTH.md](ARCHITECTURE_REVIEW_CITATION_PERSISTENCE_006Z-PREAUTH.md)
- [CITATION_ASSEMBLY_CONTRACT.md](CITATION_ASSEMBLY_CONTRACT.md)
- [LEGAL_OBJECT_PROMOTION_CONTRACT.md](LEGAL_OBJECT_PROMOTION_CONTRACT.md)
- Migration `b5c3e9a04d47` (promotion persistence reference)
- [OPEN_DECISIONS.md](OPEN_DECISIONS.md) (OD-021)

# Retrieval Persistence Remediation — TASK-007C1

## Purpose

Authoritative remediation specification for future **TASK-007C** retrieval persistence, addressing findings from [`ARCHITECTURE_REVIEW_RETRIEVAL_PERSISTENCE_007C-PREAUTH.md`](ARCHITECTURE_REVIEW_RETRIEVAL_PERSISTENCE_007C-PREAUTH.md).

**This document modifies planned architecture only.** It does not implement persistence, migrations, models, services, workers, APIs, ranking, answers, or AI search.

| Item | Status |
|------|--------|
| TASK-007C pre-auth review | **Complete** — APPROVED WITH REQUIRED REMEDIATION BEFORE 007C |
| TASK-007C1 remediation package | **Complete** — RP-01 through RP-08 addressed at governance level |
| TASK-007C1 acceptance review | **CLOSED** — [`RETRIEVAL_PERSISTENCE_007C1_ACCEPTANCE_REVIEW.md`](RETRIEVAL_PERSISTENCE_007C1_ACCEPTANCE_REVIEW.md) |
| TASK-007C implementation | **AUTHORIZED WITH CONDITIONS** |

---

## Remediation index

| Finding | Severity | Section | Status |
|---------|----------|---------|--------|
| RP-01 | HIGH | Request hash JSON canonicalization | **Addressed** |
| RP-02 | HIGH | FK constraints on evidence references | **Addressed** |
| RP-03 | HIGH | Citation-reference consistency | **Addressed** |
| RP-04 | MEDIUM | DB CHECK constraints | **Addressed** |
| RP-05 | MEDIUM | `deterministic_order_index` | **Addressed** |
| RP-06 | HIGH | `evidence_metadata` whitelist | **Addressed** |
| RP-07 | LOW | Zero-result semantics | **Addressed** |
| RP-08 | LOW | Mechanical prohibited-field tests | **Addressed** |

---

## RP-01 — Request hash canonicalization

### Formula

```text
request_hash = SHA-256(canonical_json(normalized_retrieval_envelope))
```

### Canonical JSON rules (mandatory)

Logically equivalent `scope_envelope` JSON **must** produce the same `request_hash`.

| Rule | Requirement |
|------|-------------|
| Key ordering | Lexicographic sort of object keys at every nesting level |
| Whitespace | No insignificant whitespace — compact serialization |
| Encoding | UTF-8 |
| Null handling | Explicit `null` in envelope; omit vs null policy fixed per field spec below |
| Empty object | `{}` serializes as `{}` |
| Empty list | `[]` serializes as `[]` |
| Booleans | JSON literals `true` / `false` only |
| Dates | ISO 8601 date strings `YYYY-MM-DD` for `as_of_date` |
| Numbers | No floats in envelope — integers/booleans/strings/dates only |
| Serialization | Single canonical JSON string fed to SHA-256 |

### Normalized envelope fields (included in hash)

| Field | Inclusion |
|-------|-----------|
| `retrieval_mode` | Required |
| `as_of_date` | Included when mode = `AS_OF_DATE`; omitted otherwise |
| `legal_object_version_id` | Included when mode = `EXACT_VERSION`; omitted otherwise |
| `jurisdiction_code` | Required |
| `tax_type_code` | Included (null → JSON `null`) |
| `scope_envelope` | Required object — canonical nested JSON |
| `include_canonical_text` | Required boolean |
| `include_rendered_citation_text` | Required boolean |
| `contract_version` | Optional schema generation tag when multiple envelope versions exist |

### `scope_envelope` shape (hash input)

Stable keys only (alphabetical in canonical JSON):

```json
{
  "legal_object_id": null,
  "legal_object_type": null,
  "object_identifier": null,
  "source_document_id": null,
  "source_version_id": null
}
```

Unset filters → `null`. No omitted keys at this level.

### Excluded from hash (audit metadata only)

- raw `query_text`
- `requested_by_actor_type` / `requested_by_actor_identifier`
- `requested_at` / timestamps
- `notes`
- database IDs (`retrieval_request_id`)
- `force_replay` (replay uses distinct hash material per 006Z precedent)

### Default vs force replay

| Mode | Hash material |
|------|----------------|
| Default (`force_replay=false`) | Canonical envelope above |
| Force replay (`force_replay=true`) | Envelope + `force_replay=true` + replay nonce (`retrieval_request_id` or dedicated nonce) |

---

## RP-02 — FK constraints on evidence references

### Doctrine

Evidence rows must **not** point to non-existent legal memory. **No orphan references.**

### Table: `retrieval_evidence_references` (planned)

| Column | FK target | Nullable |
|--------|-----------|----------|
| `legal_object_id` | `legal_objects.legal_object_id` | NOT NULL |
| `legal_object_version_id` | `legal_object_versions.legal_object_version_id` | NOT NULL |
| `source_version_id` | `source_versions.id` | NOT NULL |
| `citation_id` | `citations.citation_id` | NULLABLE |

**FKs are mandatory** on all non-null pin columns.

`source_document_id` may be denormalized for queryability but must match lineage resolvable through `source_version_id`.

---

## RP-03 — Citation reference consistency

### Validation rules (application layer — mandatory before persist)

When citation fields are present on an evidence reference:

| Rule | Requirement |
|------|-------------|
| Pairing | `citation_id` and `citation_hash` **both present or both absent** |
| Resolution | `citation_id` must resolve to existing `citations` row |
| Hash match | `citation_hash` must equal `citations.citation_hash` for that row |
| Version pin | `citations.legal_object_version_id` = evidence.`legal_object_version_id` |
| Object pin | `citations.legal_object_id` = evidence.`legal_object_id` |
| Source pin | `citations.source_version_id` = evidence.`source_version_id` |

### On mismatch

- Persist `retrieval_result` with `retrieval_status=failed`
- Set `error_category=provenance_incomplete` (or dedicated `citation_mismatch` if taxonomy extended)
- Populate `error_message` with explicit mismatch detail
- **Never** silently drop mismatched citation
- **Never** silently replace citation with legal-object-only reference

---

## RP-04 — DB CHECK constraints

### `retrieval_requests.retrieval_mode`

```sql
CHECK (retrieval_mode IN ('AS_OF_DATE', 'EXACT_VERSION', 'LATEST_VERSION'))
```

### `retrieval_results.retrieval_status`

```sql
CHECK (retrieval_status IN (
  'pending', 'accepted', 'completed', 'failed', 'skipped', 'duplicate_rejected'
))
```

### `retrieval_requests.requested_by_actor_type`

```sql
CHECK (requested_by_actor_type IN ('user', 'system', 'worker', 'admin', 'test'))
```

### `retrieval_results.error_category` (nullable)

```sql
CHECK (error_category IS NULL OR error_category IN (
  'invalid_request',
  'temporal_scope_missing',
  'version_missing',
  'citation_missing',
  'provenance_incomplete',
  'duplicate_retrieval',
  'retrieval_pipeline_unavailable',
  'unknown_failure'
))
```

---

## RP-05 — Deterministic order index

### DB constraint

```text
UNIQUE(retrieval_result_id, deterministic_order_index)
```

### Derivation rules

1. Assigned **after** explicit deterministic `ORDER BY` in retrieval execution (007D).
2. Starts at **1** per `retrieval_result_id`.
3. Increments by 1 for each evidence reference in sort order.
4. Represents **order only** — not ranking, relevance, or confidence.

```text
deterministic_order_index ≠ ranking_score
```

---

## RP-06 — `evidence_metadata` whitelist

### Doctrine

`evidence_metadata` is **strictly whitelisted** JSON. Unknown keys **rejected**. Prohibited keys **rejected**. Metadata must be **non-interpretive**.

### Allowed keys only

| Key | Purpose |
|-----|---------|
| `structural_path` | Structural location in source |
| `source_label` | Source document label (stored metadata) |
| `citation_label` | Display handle — not legal meaning |
| `object_label` | Legal object structural label |
| `object_type` | Structural type enum |
| `location_reference` | Citation location string |
| `deterministic_sort_key` | Sort tie-break material (not score) |
| `provenance_notes` | Operator audit notes — non-interpretive |

### Prohibited keys (reject at validation)

- `answer_text`
- `legal_conclusion`
- `applicability_flag`
- `relevance_score`
- `ranking_score`
- `confidence_score`
- `semantic_score`
- `ai_output`
- `llm_output`
- `recommendation`
- `advice`
- `interpretation`

### Validation

- Service layer: reject unknown/prohibited keys before insert
- Future tests (RP-08): mechanical enforcement

---

## RP-07 — Zero-result semantics

| State | Meaning |
|-------|---------|
| `retrieval_status = completed` | Retrieval orchestration succeeded |
| `result_count = 0` | **Successful empty retrieval** — valid outcome |

### Rules

1. Zero results is **not** failure.
2. Zero results must **not** be interpreted as answer absence or legal conclusion.
3. Zero results must **not** trigger applicability inference.
4. `completed_at` populated; no `error_category` on success path.

---

## RP-08 — Mechanical prohibited-field tests (007C / 007D)

Future tests must verify:

| Check | Method |
|-------|--------|
| Prohibited columns absent | Schema introspection — no `answer_*`, `ranking_*`, `relevance_*`, `confidence_*`, `applicability_*` on retrieval tables |
| Prohibited metadata keys rejected | Unit tests on metadata validator |
| Answer/ranking fields cannot persist | Integration tests attempting insert → rejection |
| Semantic/AI fields cannot persist | Import guard + schema guard |

Document in TASK-007C test plan; implement with 007C migration tests.

---

## Planned TASK-007C schema (authoritative after 007C1)

### Table: `retrieval_requests`

| Column | Type / constraint |
|--------|-------------------|
| `id` | UUID PK |
| `request_hash` | String(64) NOT NULL, indexed |
| `retrieval_mode` | String(64) NOT NULL, CHECK RP-04 |
| `as_of_date` | Date, nullable |
| `legal_object_version_id` | UUID FK, nullable |
| `jurisdiction_code` | String(16) NOT NULL |
| `tax_type_code` | String(64), nullable |
| `scope_envelope` | JSONB NOT NULL |
| `include_canonical_text` | Boolean NOT NULL default false |
| `include_rendered_citation_text` | Boolean NOT NULL default false |
| `requested_by_actor_type` | String(64) NOT NULL, CHECK RP-04 |
| `requested_by_actor_identifier` | String(255), nullable |
| `requested_at` | Timestamptz NOT NULL |
| `force_replay` | Boolean NOT NULL default false |
| `query_text` | Text, nullable — **not in request_hash** |
| `notes` | Text, nullable |
| `created_at` | Timestamptz NOT NULL |

**Indexes / constraints:**

- Partial unique: `request_hash` WHERE `force_replay = false` (or envelope-specific partial unique per final 007C spec)
- Index on `request_hash`
- CHECK constraints per RP-04

### Table: `retrieval_results`

| Column | Type / constraint |
|--------|-------------------|
| `id` | UUID PK |
| `retrieval_request_id` | UUID FK → `retrieval_requests.id`, NOT NULL |
| `retrieval_status` | String(64) NOT NULL, CHECK RP-04 |
| `result_count` | Integer, nullable |
| `completed_at` | Timestamptz, nullable |
| `error_category` | String(64), nullable, CHECK RP-04 |
| `error_message` | Text, nullable |
| `notes` | Text, nullable |
| `created_at` | Timestamptz NOT NULL |

**Prohibited on result:** answer text, rankings, scores, interpretations, evidence payloads (evidence in child table).

### Table: `retrieval_evidence_references`

| Column | Type / constraint |
|--------|-------------------|
| `id` | UUID PK |
| `retrieval_result_id` | UUID FK → `retrieval_results.id`, NOT NULL |
| `deterministic_order_index` | Integer NOT NULL |
| `legal_object_id` | String(64) FK → `legal_objects`, NOT NULL |
| `legal_object_version_id` | UUID FK → `legal_object_versions`, NOT NULL |
| `source_version_id` | UUID FK → `source_versions`, NOT NULL |
| `citation_id` | String(255) FK → `citations.citation_id`, nullable |
| `citation_hash` | String(64), nullable |
| `evidence_metadata` | JSONB, nullable — whitelist RP-06 |
| `created_at` | Timestamptz NOT NULL |

**Constraints:**

- `UNIQUE(retrieval_result_id, deterministic_order_index)` — RP-05
- FK constraints per RP-02
- CHECK: citation_id/citation_hash pairing enforced at service layer (RP-03)

### ORM naming (planned)

- `RetrievalRequest` → `retrieval_requests`
- `RetrievalResult` → `retrieval_results`
- `RetrievalEvidenceReference` → `retrieval_evidence_references`

Distinct from `source_retrieval_log` (ingestion monitoring).

---

## OD-021 carry-forward

- Single-worker retrieval persistence acceptable initially
- Concurrent workers require `request_hash`-keyed advisory/row locks — document only; implement in 007D if concurrency authorized

---

## Authorization gate (TASK-007C)

1. TASK-007C pre-auth review accepted — **done**
2. TASK-007C1 remediation package accepted — **done**
3. TASK-007C1 acceptance review **CLOSED** — **TASK-007C AUTHORIZED WITH CONDITIONS** ([`RETRIEVAL_PERSISTENCE_007C1_ACCEPTANCE_REVIEW.md`](RETRIEVAL_PERSISTENCE_007C1_ACCEPTANCE_REVIEW.md))

Retrieval execution (007D), ranking, answers, and AI remain **not authorized**.

---

## References

- [`ARCHITECTURE_REVIEW_RETRIEVAL_PERSISTENCE_007C-PREAUTH.md`](ARCHITECTURE_REVIEW_RETRIEVAL_PERSISTENCE_007C-PREAUTH.md)
- [`RETRIEVAL_RUNTIME_CONTRACT.md`](RETRIEVAL_RUNTIME_CONTRACT.md)
- [`CITATION_PERSISTENCE_REMEDIATION_006ZA.md`](CITATION_PERSISTENCE_REMEDIATION_006ZA.md) (precedent)

---

## Acceptance criteria (007C1)

- [x] RP-01 through RP-06 addressed
- [x] RP-05, RP-07, RP-08 included
- [x] Planned TASK-007C schema documented
- [x] No implementation introduced
- [x] TASK-007C1 acceptance review **CLOSED** — TASK-007C authorized with conditions

---

END OF RETRIEVAL PERSISTENCE REMEDIATION 007C1

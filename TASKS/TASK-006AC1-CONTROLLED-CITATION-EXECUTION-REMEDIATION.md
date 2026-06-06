# TASK-006AC1 — Controlled Citation Execution Remediation Package

## Status

**Complete** — governance-only remediation package delivered; **acceptance review complete** — TASK-006AD **authorized with conditions** (implementation not yet started).

## Important

- **Does NOT implement TASK-006AD**
- **TASK-006AD authorized with conditions** — bounded implementation not yet started
- No citation entity, migrations, workers, rendering execution, retrieval, ranking, or answers
- No modifications to existing citation persistence or governance worker code

## Objective

Close remaining **006AC** blockers **AC-02** and **AC-03** at the architecture/governance level by producing the authoritative specification required before controlled citation execution may be authorized.

## Source review

Findings from [`TASK-006AC-CONTROLLED-CITATION-EXECUTION-PREAUTH-REVIEW.md`](TASK-006AC-CONTROLLED-CITATION-EXECUTION-PREAUTH-REVIEW.md):

| Finding | Status before 006AC1 | Status after 006AC1 |
|---------|----------------------|---------------------|
| AC-01 HIGH — temporal fallback | Open | **Closed (TASK-004E)** |
| AC-02 HIGH — citation identity / 004D tuple | Open | **Remediated (spec)** |
| AC-03 MEDIUM — DB UNIQUE on citation identity | Open | **Remediated (spec)** |

## Canonical artifacts

| Artifact | Path |
|----------|------|
| Remediation specification | [`CITATION_EXECUTION_REMEDIATION_006AC1.md`](../CITATION_EXECUTION_REMEDIATION_006AC1.md) |
| Pre-auth review | [`TASK-006AC-CONTROLLED-CITATION-EXECUTION-PREAUTH-REVIEW.md`](TASK-006AC-CONTROLLED-CITATION-EXECUTION-PREAUTH-REVIEW.md) |
| 004D assembler contract | [`backend/app/services/citation/CITATION_ASSEMBLY_CONTRACT.md`](../backend/app/services/citation/CITATION_ASSEMBLY_CONTRACT.md) |
| Temporal remediation | [`TASKS/TASK-004E-CITATION-TEMPORAL-COMPLIANCE-REMEDIATION.md`](TASK-004E-CITATION-TEMPORAL-COMPLIANCE-REMEDIATION.md) |
| Task record | `TASKS/TASK-006AC1-CONTROLLED-CITATION-EXECUTION-REMEDIATION.md` |

## Remediations delivered

### AC-02 — Canonical citation identity

- `citation_hash = SHA-256(source_version_id | legal_object_id | legal_object_version_id | location_reference)`
- Identity independent of rendering, formatting, presentation, and governance `request_hash`
- `force_reassembly` may create new execution events — must not create new `citation_hash`

### AC-03 — Uniqueness doctrine

- Future citation entity: `UNIQUE(citation_hash)` + service-level lookup
- Execution idempotency keys on `citation_hash` — not `request_hash`

### Additional specifications

- Citation identity lifecycle (`legal_object_version` → `location_reference` → `citation_hash` → entity)
- Planned citation entity required/prohibited fields
- Governance result boundary (lifecycle-only; no `citation_hash` or rendered text)
- OD-021 carry-forward (single-worker now; `citation_hash`-keyed locks for future concurrency)
- Planned 006AD authoritative flow

## Explicit prohibitions

- no Alembic migrations
- no citation entity tables or ORM models
- no controlled citation execution worker changes
- no `CitationAssembler` invocation from governance worker
- no retrieval, ranking, answers, AI

## Acceptance criteria

- [x] Remediation package exists
- [x] AC-02 addressed at governance level
- [x] AC-03 addressed at governance level
- [x] Citation identity doctrine documented
- [x] Uniqueness doctrine documented
- [x] Future citation entity shape documented
- [x] Governance result boundary documented
- [x] OD-021 carry-forward documented
- [x] Planned 006AD architecture documented
- [x] Governance docs updated
- [x] No implementation introduced
- [x] TASK-006AD remains NOT AUTHORIZED

## Next gate

**TASK-006AD bounded implementation** — authorized with conditions per 006AC1 acceptance review; implementation **not yet started**. See [`TASK-006AC-CONTROLLED-CITATION-EXECUTION-PREAUTH-REVIEW.md`](TASK-006AC-CONTROLLED-CITATION-EXECUTION-PREAUTH-REVIEW.md) for full chain.

---

END OF TASK-006AC1

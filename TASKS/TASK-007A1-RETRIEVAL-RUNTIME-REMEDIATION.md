# TASK-007A1 — Retrieval Runtime Remediation Package

## Status

**Complete** — governance-only remediation package delivered; **awaiting acceptance review** before TASK-007B authorization.

## Important

- **Does NOT implement TASK-007B**
- **TASK-007B remains NOT AUTHORIZED**
- No tables, migrations, workers, APIs, ranking, answers, or AI search
- **Does not modify TASK-004A** behavior on `main`

## Objective

Close blocking **007A** findings **R-01 through R-06** at the architecture/governance level by producing the authoritative specification required before retrieval runtime may be authorized.

## Source review

Findings from [`ARCHITECTURE_REVIEW_RETRIEVAL_RUNTIME_007A-PREAUTH.md`](../ARCHITECTURE_REVIEW_RETRIEVAL_RUNTIME_007A-PREAUTH.md):

| Finding | Status after 007A1 |
|---------|-------------------|
| R-01 HIGH — implicit latest | **Remediated (spec)** |
| R-02 HIGH — missing version pin | **Remediated (spec)** |
| R-03 HIGH — canonical_text collapse | **Remediated (spec)** |
| R-04 HIGH — no persistence doctrine | **Remediated (spec)** |
| R-05 HIGH — no citation path | **Remediated (spec)** |
| R-06 MEDIUM — ordering gap | **Remediated (spec)** |

## Canonical artifacts

| Artifact | Path |
|----------|------|
| Remediation specification | [`RETRIEVAL_RUNTIME_REMEDIATION_007A1.md`](../RETRIEVAL_RUNTIME_REMEDIATION_007A1.md) |
| Pre-auth review | [`ARCHITECTURE_REVIEW_RETRIEVAL_RUNTIME_007A-PREAUTH.md`](../ARCHITECTURE_REVIEW_RETRIEVAL_RUNTIME_007A-PREAUTH.md) |
| 004A baseline | [`backend/app/services/retrieval/LEGAL_OBJECT_RETRIEVAL_CONTRACT.md`](../backend/app/services/retrieval/LEGAL_OBJECT_RETRIEVAL_CONTRACT.md) |
| Task record | `TASKS/TASK-007A1-RETRIEVAL-RUNTIME-REMEDIATION.md` |

## Remediations delivered

### R-01 — No silent latest

- Runtime requires explicit `retrieval_mode`: `AS_OF_DATE`, `EXACT_VERSION`, or `LATEST_VERSION`
- `effective_on=None` must not imply latest in runtime

### R-02 — Version-pinned evidence

- Every evidence item requires `legal_object_id`, `legal_object_version_id`, `source_version_id`

### R-03 — Evidence references, not content

- Default output: citation + version references + provenance
- `canonical_text` / `rendered_citation_text` opt-in only

### R-04 — Persistence doctrine

- Planned `retrieval_requests` / `retrieval_results` append-only tables
- `request_hash` = lifecycle identity (not query text)

### R-05 — Citation references

- Read `citations` entity; provenance chain validation
- No re-assembly during retrieval

### R-06 — Deterministic ordering

- Explicit `ORDER BY` before single-row selection; no implicit DB order

### Additional specifications

- Ranking boundary (`ordering ≠ ranking`)
- OD-021 single-worker carry-forward
- Planned 007B authoritative flow

## Explicit prohibitions

- no Alembic migrations
- no retrieval ORM models
- no retrieval workers
- no HTTP/API routes
- no semantic/vector/AI search
- no ranking or answer generation
- no 004A code changes in this task

## Acceptance criteria

- [x] Remediation package exists
- [x] R-01 through R-06 addressed at governance level
- [x] Retrieval identity doctrine documented
- [x] Persistence doctrine documented
- [x] Citation-reference doctrine documented
- [x] Ranking boundary documented
- [x] OD-021 documented
- [x] Planned 007B flow documented
- [x] Governance docs updated
- [x] No implementation introduced
- [x] TASK-007B remains NOT AUTHORIZED

## Next gate

**Remediation acceptance review** for 007A1 package — then bounded TASK-007B authorization (not yet granted).

---

END OF TASK-007A1

# TASK-006ZA — Citation Persistence Pre-Authorization Remediation Package

## Status

**Complete** — governance and planning only

## Important

- **Does NOT implement TASK-006Z**
- **TASK-006Z remains NOT AUTHORIZED**
- No tables, migrations, models, services, workers, execution, retrieval, or answers

## Objective

Address blocking and recommended findings from [`ARCHITECTURE_REVIEW_CITATION_PERSISTENCE_006Z-PREAUTH.md`](../ARCHITECTURE_REVIEW_CITATION_PERSISTENCE_006Z-PREAUTH.md) by producing the authoritative planned persistence specification for TASK-006Z.

## Canonical artifacts

| Artifact | Path |
|----------|------|
| Remediation specification | [`CITATION_PERSISTENCE_REMEDIATION_006ZA.md`](../CITATION_PERSISTENCE_REMEDIATION_006ZA.md) |
| Pre-auth review | [`ARCHITECTURE_REVIEW_CITATION_PERSISTENCE_006Z-PREAUTH.md`](../ARCHITECTURE_REVIEW_CITATION_PERSISTENCE_006Z-PREAUTH.md) |
| Upstream contract | [`CITATION_ASSEMBLY_CONTRACT.md`](../CITATION_ASSEMBLY_CONTRACT.md) (TASK-006Y) |
| Task record | `TASKS/TASK-006ZA-CITATION-PERSISTENCE-REMEDIATION-PACKAGE.md` |

## Prerequisites

- TASK-006Y complete — citation governance established
- ARCHITECTURE_REVIEW 006Z-PREAUTH — **APPROVED WITH REQUIRED REMEDIATION**

## Remediations delivered

| Finding | Remediation |
|---------|-------------|
| Z-01 HIGH | `legal_object_id` + `legal_object_version_id` on request/result; version↔object validation |
| Z-02 MEDIUM | `source_version_id` denormalized on request; lineage validation |
| Z-03 HIGH | `CitationAssemblyGovernanceRequest` / `Result` — no 004D name collision |
| Z-04 MEDIUM | Full result shape with denormalized pins, `notes`, nullable `citation_id` |
| Z-05 LOW | `assembled_at` (not `completed_at`) |
| Z-07 INFO | Dual-hash: `request_hash` vs 004D rendered citation hash |
| Z-14 MEDIUM | OD-021 documented — single-worker now; locks in future worker task |

## Planned TASK-006Z shape (summary)

**Request:** `legal_object_id`, `legal_object_version_id`, `source_version_id`, `citation_reason`, actor fields, `requested_at`, `force_reassembly`, `request_hash`, `notes`

**Result:** `citation_assembly_request_id`, `legal_object_id`, `legal_object_version_id`, `citation_status`, `citation_id` (nullable), `assembled_at`, error fields, `notes`

See full column-level spec in [`CITATION_PERSISTENCE_REMEDIATION_006ZA.md`](../CITATION_PERSISTENCE_REMEDIATION_006ZA.md).

## Explicit prohibitions

- no Alembic migrations
- no SQLAlchemy models for citation assembly persistence
- no citation entity tables
- no workers or execution
- no retrieval, ranking, answers, AI

## Acceptance criteria

| Criterion | Met |
|-----------|-----|
| Remediation package exists | Yes |
| Z-01, Z-02, Z-03, Z-04, Z-05, Z-07, Z-14 addressed | Yes |
| Updated 006Z planned shape documented | Yes |
| Governance docs updated | Yes |
| No implementation introduced | Yes |
| TASK-006Z not authorized | Yes |

## Next gate

1. **Remediation acceptance** — confirm 006ZA spec satisfies pre-auth review checklist.
2. **Separate authorization** — explicit approval to implement TASK-006Z (tables + service layer only; still no execution).

## Final principle

TASK-006ZA modifies the **planned** architecture. It does not implement citation persistence.

# TASK-006AC — Controlled Citation Execution Pre-Authorization Review

## Status

**CLOSED**

## Review type

Architecture / governance review — **not** implementation.

## Verdict

**APPROVED WITH REQUIRED REMEDIATION BEFORE TASK-006AD**

This review evaluated whether controlled citation execution could be **considered** after remediation. It did **not** authorize citation execution, retrieval, ranking, answers, or legal advice by itself.

---

## Purpose

Pre-authorization review of the proposed path from citation assembly governance (TASK-006Z / 006AB) to **controlled citation execution** (future TASK-006AD): deterministic rendering via TASK-004D `CitationAssembler`, citation entity persistence, and governance result handoff.

**Authority:** [`CITATION_ASSEMBLY_CONTRACT.md`](../CITATION_ASSEMBLY_CONTRACT.md), [`backend/app/services/citation/CITATION_ASSEMBLY_CONTRACT.md`](../backend/app/services/citation/CITATION_ASSEMBLY_CONTRACT.md), [`CITATION_PERSISTENCE_REMEDIATION_006ZA.md`](../CITATION_PERSISTENCE_REMEDIATION_006ZA.md), [`TEMPORAL_VERSIONING_ARCHITECTURE.md`](../TEMPORAL_VERSIONING_ARCHITECTURE.md).

**Record note:** This artifact was reconstructed and permanently recorded as **TASK-006AC-GOV** because the original review occurred and produced blockers AC-01 through AC-07, but the canonical repository record was missing at time of TASK-006AC1 delivery.

---

## Executive summary

Controlled citation execution is **architecturally viable** only when:

1. Temporal compliance is restored (no silent source-version date inheritance).
2. Citation identity is locked to the 004D provenance tuple — independent of rendering.
3. Future citation entity enforces `UNIQUE(citation_hash)` with service-level lookup.
4. Governance results remain lifecycle-only; citation content lives on the citation entity.
5. Concurrent execution risks (OD-021) are documented before multi-worker enablement.

TASK-006AD was **not** authorized by this review alone. Remediation and acceptance were required first.

---

## Findings

### AC-01 — HIGH

| Field | Value |
|-------|--------|
| **Title** | 004D effective-date fallback creates temporal inference |
| **Risk** | `CitationAssembler` silently fell back from `legal_object_version` effective dates to `source_version` effective dates, risking durable temporal inference in rendered citations. |
| **Required remediation** | Remove silent fallback; preserve unknown legal-object dates; label source-version dates as metadata only. |
| **Resolution** | **Closed** by [TASK-004E Citation Temporal Compliance Remediation](TASK-004E-CITATION-TEMPORAL-COMPLIANCE-REMEDIATION.md). |

### AC-02 — HIGH

| Field | Value |
|-------|--------|
| **Title** | Citation identity must conform to 004D provenance tuple |
| **Risk** | Identity must not depend on rendered citation content, formatting, whitespace, metadata ordering, or presentation changes. |
| **Required formula** | `citation_hash = SHA-256(source_version_id \| legal_object_id \| legal_object_version_id \| location_reference)` |
| **Resolution** | **Remediated** by [TASK-006AC1](../CITATION_EXECUTION_REMEDIATION_006AC1.md) — see §AC-02. |

### AC-03 — MEDIUM

| Field | Value |
|-------|--------|
| **Title** | Citation identity requires DB uniqueness |
| **Risk** | Citation entity must prevent duplicate canonical citation identity under concurrent or replayed execution. |
| **Required** | `UNIQUE(citation_hash)` plus service lookup before insert. Execution idempotency keys on `citation_hash`, not `request_hash`. |
| **Resolution** | **Remediated** by [TASK-006AC1](../CITATION_EXECUTION_REMEDIATION_006AC1.md) — see §AC-03. |

### AC-04 — MEDIUM (carry-forward)

| Field | Value |
|-------|--------|
| **Title** | Citation entity must denormalize provenance and carry no interpretive fields |
| **Risk** | Mixing retrieval, ranking, applicability, or legal-meaning fields into citation storage would collapse the doctrine chain. |
| **Required** | Entity stores provenance pins and rendered text only; no interpretive or downstream-runtime fields. |
| **Resolution** | **Remediated** by [TASK-006AC1](../CITATION_EXECUTION_REMEDIATION_006AC1.md) — planned entity shape §Planned citation entity. |

### AC-05 — MEDIUM (carry-forward)

| Field | Value |
|-------|--------|
| **Title** | Citation assembly governance result must remain lifecycle-only |
| **Risk** | Storing `citation_hash`, rendered text, or retrieval metadata on governance results conflates orchestration with citation content. |
| **Required** | Results carry `citation_id` pointer, status, timestamps, and error metadata only. |
| **Resolution** | **Remediated** by [TASK-006AC1](../CITATION_EXECUTION_REMEDIATION_006AC1.md) — §Governance result boundary. Implemented 006Z shape already compliant. |

### AC-06 — INFORMATIONAL (confirmed correct)

| Field | Value |
|-------|--------|
| **Title** | Dual-hash separation — `request_hash` ≠ `citation_hash` |
| **Assessment** | TASK-006ZA / 006Z persistence correctly separates governance lifecycle identity (`request_hash`) from canonical citation identity (`citation_hash`). |
| **Resolution** | **No remediation required** — doctrine confirmed; documented in 006AC1 §Dual-hash doctrine. |

### AC-07 — MEDIUM (carry-forward — OD-021)

| Field | Value |
|-------|--------|
| **Title** | Concurrent citation execution race |
| **Risk** | `UNIQUE(citation_hash)` alone is insufficient under concurrent workers; read-check-then-act races may duplicate work. |
| **Required** | Single-worker acceptable on `main` now. Future concurrent citation execution requires `citation_hash`-keyed advisory or row locking in addition to DB uniqueness. |
| **Resolution** | **Carry-forward** documented in [TASK-006AC1](../CITATION_EXECUTION_REMEDIATION_006AC1.md) §OD-021 — implement in TASK-006AD when concurrent workers are enabled. |

---

## What 006AC did NOT authorize

| Capability | Authorized by 006AC? |
|------------|---------------------|
| Controlled citation execution (006AD) | **No** — remediation required first |
| Citation entity / migrations | **No** |
| Citation rendering in governance worker | **No** |
| Retrieval | **No** |
| Ranking | **No** |
| Answer generation | **No** |
| Legal advice / legal meaning | **No** |
| Applicability inference | **No** |

006AC only reviewed whether controlled citation execution **could be considered** after remediation closed the blockers above.

---

## Required remediation sequence (outcome)

```text
TASK-006AC Review (this document)
  → TASK-004E — closed AC-01
  → TASK-006AC1 — remediated AC-02 and AC-03 (and documented AC-04–AC-07)
  → TASK-006AC1 Acceptance Review — authorized TASK-006AD with conditions
  → TASK-006AD — bounded implementation (authorized with conditions; not yet started)
```

| Step | Status |
|------|--------|
| TASK-006AC pre-auth review | **CLOSED** — this record |
| TASK-004E (AC-01) | **Complete** |
| TASK-006AC1 (AC-02 / AC-03) | **Complete** |
| TASK-006AC1 acceptance review | **Complete** — TASK-006AD authorized with conditions |
| TASK-006AD implementation | **Authorized with conditions** — **not yet started** |

### Conditions on TASK-006AD authorization

Bounded implementation must:

- Use 004D `CitationAssembler` only for deterministic rendering — no retrieval, ranking, answers, or inference.
- Persist citation entity with `UNIQUE(citation_hash)` and service lookup per 006AC1.
- Keep governance results lifecycle-only (`citation_id` pointer only).
- Preserve TASK-004E temporal compliance.
- Remain single-worker until OD-021 execution-time locks are implemented for concurrency.

---

## Doctrine chain (preserved)

```text
parsed_structure ≠ legal_object
legal_object ≠ legal meaning
legal_object ≠ citation
citation ≠ retrieval
citation ≠ answer
```

Citation identity is derived from **provenance**, not from rendering, retrieval, or answers.

---

## Related artifacts

| Artifact | Path |
|----------|------|
| Temporal remediation (AC-01) | [`TASKS/TASK-004E-CITATION-TEMPORAL-COMPLIANCE-REMEDIATION.md`](TASK-004E-CITATION-TEMPORAL-COMPLIANCE-REMEDIATION.md) |
| Execution remediation (AC-02 / AC-03) | [`CITATION_EXECUTION_REMEDIATION_006AC1.md`](../CITATION_EXECUTION_REMEDIATION_006AC1.md) |
| Remediation task record | [`TASKS/TASK-006AC1-CONTROLLED-CITATION-EXECUTION-REMEDIATION.md`](TASK-006AC1-CONTROLLED-CITATION-EXECUTION-REMEDIATION.md) |
| 004D assembler | [`backend/app/services/citation/CITATION_ASSEMBLY_CONTRACT.md`](../backend/app/services/citation/CITATION_ASSEMBLY_CONTRACT.md) |
| Governance persistence | [`CITATION_PERSISTENCE_REMEDIATION_006ZA.md`](../CITATION_PERSISTENCE_REMEDIATION_006ZA.md) |

---

## Acceptance criteria (006AC review record)

- [x] AC-01 / AC-02 / AC-03 documented with risk and resolution
- [x] AC-04 / AC-05 / AC-06 / AC-07 documented
- [x] Remediation sequence and 006AD authorization chain documented
- [x] 006AC boundary (no execution / retrieval / answers) documented
- [x] No code changes introduced by this record

---

END OF TASK-006AC PRE-AUTHORIZATION REVIEW

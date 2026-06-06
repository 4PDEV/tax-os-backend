# Architecture Review — Retrieval Persistence Pre-Authorization (TASK-007C)

**Review type:** Pre-authorization architecture review only — **not** persistence implementation  
**Date:** 2026-06-02  
**Scope:** Planned TASK-007C append-only retrieval persistence (`retrieval_requests`, `retrieval_results`, `retrieval_evidence_references`)  
**Authority:** [`RETRIEVAL_RUNTIME_CONTRACT.md`](RETRIEVAL_RUNTIME_CONTRACT.md), [`RETRIEVAL_RUNTIME_REMEDIATION_007A1.md`](RETRIEVAL_RUNTIME_REMEDIATION_007A1.md)

**Verdict:** **APPROVED WITH REQUIRED REMEDIATION BEFORE TASK-007C**

---

## Executive summary

Planned retrieval persistence shape is **structurally sound** and aligned with citation governance (006Z) and retrieval contract (007B). Five **blocking refinements** and three **recommended refinements** must be specified before implementation may be authorized.

Remediation is required in **TASK-007C1** before TASK-007C implementation.

---

## Findings

| ID | Severity | Title | Blocks 007C? |
|----|----------|-------|--------------|
| RP-01 | HIGH | `request_hash` JSON canonicalization undefined | **Yes** |
| RP-02 | HIGH | Evidence-reference provenance pins lack FK constraints | **Yes** |
| RP-03 | HIGH | Citation-reference consistency unspecified | **Yes** |
| RP-04 | MEDIUM | DB CHECK constraints not specified | **Yes** |
| RP-05 | MEDIUM | `deterministic_order_index` uniqueness + derivation | Recommended |
| RP-06 | HIGH | `evidence_metadata` unconstrained leakage vector | **Yes** |
| RP-07 | LOW | Zero-result semantics undocumented | Recommended |
| RP-08 | LOW | Prohibited-field doctrine not mechanically testable | Recommended |

---

## What 007C review does NOT authorize

- Migrations, ORM, services, workers, APIs
- Retrieval execution, ranking, answers, AI search
- Modification of TASK-004A

---

## Required sequence

```text
TASK-007C Pre-Auth Review (this document)
  → TASK-007C1 Remediation Package
  → TASK-007C1 Acceptance Review (future)
  → TASK-007C Implementation (not authorized)
```

---

END OF TASK-007C PRE-AUTHORIZATION REVIEW

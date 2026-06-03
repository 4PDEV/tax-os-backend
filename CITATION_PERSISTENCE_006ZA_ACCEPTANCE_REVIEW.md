# TASK-006ZA Acceptance Review — Citation Persistence Remediation

**Review type:** Remediation acceptance — authorizes TASK-006Z implementation scope only  
**Date:** 2026-06-03  
**Closure date:** 2026-06-03  
**Authority:** [`CITATION_PERSISTENCE_REMEDIATION_006ZA.md`](CITATION_PERSISTENCE_REMEDIATION_006ZA.md), [`ARCHITECTURE_REVIEW_CITATION_PERSISTENCE_006Z-PREAUTH.md`](ARCHITECTURE_REVIEW_CITATION_PERSISTENCE_006Z-PREAUTH.md)

**Verdict:** **CLOSED** — **TASK-006Z AUTHORIZED FOR IMPLEMENTATION**

---

## Findings closed

| ID | Finding | Status |
|----|---------|--------|
| Z-01 | `legal_object_id` on request/result | **CLOSED** |
| Z-02 | `source_version_id` denormalization | **CLOSED** |
| Z-03 | Namespace separation from TASK-004D | **CLOSED** |
| Z-04 | Complete result shape | **CLOSED** |
| Z-05 | `assembled_at` naming | **CLOSED** |
| Z-07 | Dual-hash doctrine | **CLOSED** |
| Z-14 | OD-021 carry-forward | **CLOSED** |

---

## Platform state after acceptance

| Layer / capability | Status |
|--------------------|--------|
| Citation governance (006Y) | **COMPLETE** |
| Citation persistence design (006ZA) | **COMPLETE** |
| Citation persistence implementation (006Z) | **AUTHORIZED** — not yet implemented |
| Citation execution | **NOT AUTHORIZED** |
| Retrieval runtime | **NOT AUTHORIZED** |
| Answer runtime | **NOT AUTHORIZED** |

---

## Authorization envelope (TASK-006Z)

**Approved for implementation only:**

| Item | Scope |
|------|--------|
| Tables | `citation_assembly_requests`, `citation_assembly_results` |
| Persistence mode | Append-only request/result rows |
| Identity | `legal_object_version_id` default; `request_hash`; `force_reassembly` |
| Lineage pins | `legal_object_id`, `legal_object_version_id`, `source_version_id` |
| Result governance | `citation_status`, `error_category`, `assembled_at`, nullable `citation_id` |
| DB guard | Partial unique on `legal_object_version_id` WHERE `force_reassembly = false` |
| ORM names | `CitationAssemblyGovernanceRequest`, `CitationAssemblyGovernanceResult` |

**Explicitly not authorized:**

- Citation execution or rendering
- Citation workers
- Citation entity / content tables
- Retrieval, ranking
- Answer generation
- Legal advice
- Tax/applicability inference
- AI/LLM usage

---

## Doctrine chain (unchanged)

`parsed_structure` ≠ legal object · `legal_object` ≠ legal meaning · `legal_object` ≠ citation · `citation` ≠ answer

---

## Future gates

Before citation **execution**, **retrieval**, or **answer assembly**, require a review checkpoint following the pattern: 006P1, 006T1A, 006X1, 006U–006X, 006ZA.

---

## References

- [CITATION_ASSEMBLY_CONTRACT.md](CITATION_ASSEMBLY_CONTRACT.md)
- [TASKS/TASK-006ZA-CITATION-PERSISTENCE-REMEDIATION-PACKAGE.md](TASKS/TASK-006ZA-CITATION-PERSISTENCE-REMEDIATION-PACKAGE.md)

# Architecture Review — Legal Object Promotion (TASK-006U through TASK-006X)

**Reviewer role:** Claude architecture review  
**Date:** 2026-06-03  
**Closure date:** 2026-06-03  
**Scope:** TASK-006U, 006V, 006W, 006X, 006X1; upstream parsing pipeline (006Q–006T1A); `LEGAL_OBJECT_PROMOTION_CONTRACT.md`  
**Verdict:** **CLOSED** — **APPROVED FOR CONTINUE**

---

## Executive summary

The legal object promotion path from governed `parsed_structure` evidence through promotion persistence, dry-run orchestration, and controlled materialization is **architecturally sound and governance-bounded**.

**639 tests pass** at 006X1 verification. Dry-run and controlled-promotion modes are explicitly gated. Controlled promotion reads **only** `parsed_structure` (and resolvable provenance rows) — no network, AI, citation, or answer generation.

**Mandatory doctrines enforced:**

| Boundary | Status |
|----------|--------|
| `parsed_structure` ≠ legal object | Promotion is governed, not automatic parsing output |
| `legal_object` ≠ legal meaning | Labels, path, text from structure; dates from `source_version` only |
| `legal_object` ≠ citation | No citation anchors in promotion path |
| `legal_object` ≠ answer | No answer assembly in promotion path |

**Identity:** `legal_object_id = ps-{parsed_structure_id}`; `force_repromotion` appends new `legal_object_version` (append-only).

Legal-object creation has **not** crossed into legal interpretation, applicability inference, or taxpayer-effect determination.

---

## Findings (closed)

| ID | Finding | Status |
|----|---------|--------|
| L-01 | LegalObjectType vocabulary structural-only | **CLOSED** |
| L-02 | Canonical legal-memory write path append-only | **CLOSED** |
| L-02b | `UNIQUE(legal_object_id, text_hash)` at DB layer | **CLOSED** — [CLAUDE_VERIFICATION_LEGAL_OBJECT_VERSION_IDENTITY_006X1.md](CLAUDE_VERIFICATION_LEGAL_OBJECT_VERSION_IDENTITY_006X1.md) (TASK-006X1) |
| — | No interpretive fields in 006X materialization | Verified |
| OD-021 | Execution-time replay race under concurrent workers | **OPEN / INFORMATIONAL** — see [OPEN_DECISIONS.md](OPEN_DECISIONS.md) |

---

## Gate closure record

| Item | Status |
|------|--------|
| TASK-006U–006X Claude review | **CLOSED** |
| Verdict | **APPROVED FOR CONTINUE** |
| Canonical Legal Memory phase | **CLOSED** |
| Citation layer | **OPEN** |
| TASK-006Y | **COMPLETE** (governance-only citation assembly contract — see [`CITATION_ASSEMBLY_CONTRACT.md`](CITATION_ASSEMBLY_CONTRACT.md)) |
| TASK-006Z | Planned after 006Y — not authorized until explicit approval |
| TASK-007A+ | Planned after citation persistence — not authorized until explicit approval |

**006Y scope boundary:** `legal_object` → citation assembly **contract** only. Still **no** citation persistence, answer generation, retrieval runtime, legal advice, or tax/applicability inference.

**Blocked until governed task approval:** citation persistence (006Z), answer runtime, retrieval runtime.

---

## References

- [LEGAL_OBJECT_PROMOTION_CONTRACT.md](LEGAL_OBJECT_PROMOTION_CONTRACT.md)
- [TASKS/TASK-006U-X-LEGAL-OBJECT-PROMOTION-REVIEWER-PACKAGE.md](TASKS/TASK-006U-X-LEGAL-OBJECT-PROMOTION-REVIEWER-PACKAGE.md)
- [CLAUDE_VERIFICATION_LEGAL_OBJECT_VERSION_IDENTITY_006X1.md](CLAUDE_VERIFICATION_LEGAL_OBJECT_VERSION_IDENTITY_006X1.md)
- [CLAUDE_REVIEW_PARSING_PIPELINE_006Q-T.md](CLAUDE_REVIEW_PARSING_PIPELINE_006Q-T.md) (upstream, closed)

# Architecture Review — Legal Object Promotion (TASK-006U through TASK-006X)

**Reviewer role:** Claude-style architecture review (post-checkpoint `checkpoint-task-006x-controlled-legal-object-promotion-execution`)  
**Date:** 2026-06-03  
**Scope:** TASK-006U, 006V, 006W, 006X; upstream parsing pipeline (006Q–006T1A); `LEGAL_OBJECT_PROMOTION_CONTRACT.md`  
**Verdict:** **CLOSED** (2026-06-03) — citation assembly gate may open via TASK-006Y when explicitly approved

---

## Executive summary

The legal object promotion path from governed `parsed_structure` evidence through promotion persistence, dry-run orchestration, and controlled materialization is **architecturally sound and governance-bounded**.

**633 tests pass** at the 006X checkpoint. Dry-run and controlled-promotion modes are explicitly gated. Controlled promotion reads **only** `parsed_structure` (and resolvable provenance rows) — no network, AI, citation, or answer generation.

**Mandatory doctrines enforced:**

| Boundary | Status |
|----------|--------|
| `parsed_structure` ≠ legal object | Promotion is governed, not automatic parsing output |
| `legal_object` ≠ legal meaning | Labels, path, text from structure; dates from `source_version` only |
| `legal_object` ≠ citation | No citation anchors in promotion path |
| `legal_object` ≠ answer | No answer assembly in promotion path |

**Identity:** `legal_object_id = ps-{parsed_structure_id}`; `force_repromotion` appends new `legal_object_version` (append-only).

**Gate satisfied:** Legal-object creation has **not** crossed into legal interpretation, applicability inference, or taxpayer-effect determination.

---

## 1. Promotion idempotency (006V / 006P1 / 006R parity)

| Mechanism | Behavior |
|-----------|----------|
| Default `promotion_hash` | SHA-256(`parsed_structure_id`) only |
| DB uniqueness | Partial unique index WHERE `force_repromotion = false` |
| Worker skip | Terminal `promoted` / `skipped` / `failed`; global `promoted` guard per structure |
| Force replay | Unique hash per force row; append-only `legal_object_version` on 006X |

Creation-time duplicate promotion is closed at persistence layer. **OD-021** execution-time race under concurrent promotion workers remains deferred (LOW single-worker; MEDIUM under concurrency).

---

## 2. Controlled materialization (006X)

| Check | Result |
|-------|--------|
| Input scope | `parsed_structure` only |
| Object identity | `ps-{parsed_structure_id}` |
| Version hash | Default: `structure_hash`; replay: `sha256(structure_hash:request_id)` |
| Temporal | `effective_from` / `effective_to` copied from `source_version` — not inferred |
| Provenance | `object_title` records structural IDs/hashes only |
| Pipeline state | `extracted` → `parsed` → `legal_objects_created` when applicable |

---

## 3. Dry-run semantics (006W)

`skipped` on a result row means **dry-run orchestration completed without promotion execution** — not that the request was ignored. Worker `requests_skipped` counts ineligible/terminal requests that never entered processing.

---

## 4. Provenance chain (citation-ready lineage)

```text
source_version → extraction_run → extracted_text → parser_run → parsed_structure → legal_object
```

No lineage break observed in implementation. Future citation assembly (006Y+) may depend on this chain.

---

## 5. Findings

| ID | Finding | Severity | Status |
|----|---------|----------|--------|
| — | No interpretive fields introduced in 006X materialization | — | Verified |
| OD-021 | Execution-time replay race under concurrent workers | LOW / MEDIUM | Deferred to citation/retrieval concurrency design |

---

## 6. Approval record

**TASK-006X COMPLETE — CONTROLLED LEGAL OBJECT PROMOTION EXECUTION ACCEPTED**

**Canonical Legal Memory phase — CLOSED** on `main` at `checkpoint-task-006x-controlled-legal-object-promotion-execution`.

**Do not proceed to citation persistence or answer runtime without governed tasks.** Approved sequence after explicit task approval:

1. TASK-006Y — Citation Assembly Contract  
2. TASK-006Z — Citation Persistence  
3. TASK-007A+ — Retrieval & Query Runtime  

---

## References

- [LEGAL_OBJECT_PROMOTION_CONTRACT.md](LEGAL_OBJECT_PROMOTION_CONTRACT.md)
- [TASKS/TASK-006U-X-LEGAL-OBJECT-PROMOTION-REVIEWER-PACKAGE.md](TASKS/TASK-006U-X-LEGAL-OBJECT-PROMOTION-REVIEWER-PACKAGE.md)
- [CLAUDE_REVIEW_PARSING_PIPELINE_006Q-T.md](CLAUDE_REVIEW_PARSING_PIPELINE_006Q-T.md) (upstream, closed)

# TASK-006U–006X — Legal Object Promotion Reviewer Package

**Purpose:** Claude review checkpoint before citation layer (006Y+).

**Status:** Review **CLOSED** (2026-06-03) — see [CLAUDE_REVIEW_LEGAL_OBJECT_PROMOTION_006U-X.md](../CLAUDE_REVIEW_LEGAL_OBJECT_PROMOTION_006U-X.md)

**Checkpoint tag:** `checkpoint-task-006x-controlled-legal-object-promotion-execution`

## Pipeline delivered

```text
source_version
  → extraction → extracted_text
  → parsing → parsed_structure
  → promotion request/result (006V)
  → promotion worker (006W dry-run | 006X controlled)
  → legal_object + legal_object_version (006X only)
```

## Governance boundaries (must remain intact)

| Boundary | Doctrine |
|----------|----------|
| `parsed_structure` | Structural evidence only (006Q–006T) |
| `parsed_structure` ≠ legal object | Promotion is governed, not automatic parsing |
| `legal_object` | Canonical legal memory (006X) — not legal meaning or advice |
| `legal_object` ≠ citation | No citation anchors in promotion path |
| `legal_object` ≠ answer | No answer assembly in promotion path |

## Review focus

1. **Non-interpretive materialization** — 006X populates labels/path/text from `parsed_structure` units only; no obligation/applicability/tax-effect inference.
2. **Identity** — `ps-{parsed_structure_id}`; one default legal object per structure; replay appends versions only.
3. **Idempotency** — DB partial unique on promotion requests; worker skip rules; `force_repromotion` replay auditable.
4. **Provenance** — `object_title` records structural IDs/hashes only; lineage chain unbroken.
5. **Temporal** — `effective_from` / `effective_to` copied from `source_version`; no silent inference.
6. **Dry-run semantics** — `skipped` = orchestration completed without execution (not request ignored).

## Test evidence

- Full suite: **633 passed** (PostgreSQL `taxos_test`)
- `test_legal_object_promotion_persistence.py`
- `test_legal_object_promotion_worker_skeleton.py`
- `test_controlled_legal_object_promotion_execution.py`

## OD-021

Creation-time idempotency closed (006V). Execution-time multi-worker replay race deferred to citation/retrieval concurrency design.

## Expected next phase (after review sign-off)

| Task | Scope |
|------|--------|
| TASK-006Y | Citation assembly contract |
| TASK-006Z | Citation persistence |
| TASK-007A+ | Retrieval and query runtime |

**Gate:** No citation/answer automation until 006U–006X review confirms legal-object creation has not crossed into legal interpretation.

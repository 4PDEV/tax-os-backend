# TASK-006X — Controlled Legal Object Promotion Execution

**Status:** Complete — accepted at `checkpoint-task-006x-controlled-legal-object-promotion-execution` (Claude review CLOSED 2026-06-03)  
**Depends on:** TASK-006W

## Scope delivered

- `ControlledLegalObjectPromotionProvider` (`controlled_legal_object_promotion_provider` @ `0.1.0`)
- `materialize_legal_object_from_parsed_structure()` — structural-only canonical memory
- `run_controlled_legal_object_promotion()` — requires `controlled_promotion=True`
- Legal object identity: `ps-{parsed_structure_id}` (one default object per structure)
- Force replay: append-only new `legal_object_version` with deterministic replay `text_hash`
- Worker modes: `dry_run` | `controlled_promotion` (terminal `promoted` with `legal_object_id`)

## Governance

- No legal meaning, citations, answers, AI, or network
- Temporal fields copied from `source_version` only (no inference)
- Provenance recorded in `object_title` (structural references only)

## Out of scope

- Citations, answers, retrieval

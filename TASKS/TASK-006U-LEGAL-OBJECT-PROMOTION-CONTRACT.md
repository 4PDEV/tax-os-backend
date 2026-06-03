# TASK-006U — Legal Object Promotion Contract

## Status

**Complete** (contract-only; governance-only)

## Objective

Define the governed contract for promoting `parsed_structure` evidence into canonical `legal_object` legal memory.

This task establishes the boundary:

```text
parsed_structure → legal_object
```

It does **not** implement promotion persistence, workers, execution, citations, or answers.

## Canonical contracts

| Artifact | Path |
|----------|------|
| Primary specification | [`LEGAL_OBJECT_PROMOTION_CONTRACT.md`](../LEGAL_OBJECT_PROMOTION_CONTRACT.md) |
| Task record | `TASKS/TASK-006U-LEGAL-OBJECT-PROMOTION-CONTRACT.md` |

## Prerequisites

- TASK-006Q–006T parsing pipeline complete
- TASK-006T1A parsed structure identity verified
- Legal-object promotion gate **open** (Claude verification 2026-06-02)
- Existing legal-object schema/persistence contracts (003A–003E) remain separate upstream governance

## Scope delivered

1. Legal object role and promotion responsibilities
2. Promotion boundary (`parsed_structure` → review → `legal_object`)
3. Eligibility rules for `parsed_structure`
4. Future `LegalObjectPromotionRequest` / `LegalObjectPromotionResult` contracts
5. Promotion status and error category taxonomies
6. Idempotency doctrine (`parsed_structure_id` canonical identity)
7. `force_repromotion` doctrine
8. `promotion_hash` doctrine
9. Provenance chain requirements
10. Temporal no-inference alignment
11. Legal-meaning and citation boundaries
12. OD-021 concurrency carry-forward

## Explicit prohibitions

- no promotion persistence tables
- no promotion workers
- no legal-object write execution in this task
- no citation or answer generation
- no legal/tax/applicability interpretation
- no AI/LLM usage

## Doctrine (critical)

| Concept | Rule |
|---------|------|
| `parsed_structure` | Structural evidence |
| `legal_object` | Canonical legal memory |
| Promotion | Governed transition — **not** automatic parsing output |

**`parsed_structure` ≠ legal object**

## Acceptance criteria

| Criterion | Met |
|-----------|-----|
| Legal object promotion contract exists | Yes |
| Request contract defined | Yes |
| Result contract defined | Yes |
| Status values defined | Yes |
| Error categories defined | Yes |
| Idempotency doctrine documented | Yes |
| Force-repromotion doctrine documented | Yes |
| Provenance doctrine documented | Yes |
| Temporal alignment documented | Yes |
| Legal-meaning boundary documented | Yes |
| Citation boundary documented | Yes |
| Docs updated | Yes |
| No persistence or execution introduced | Yes |

## Follow-on tasks (not in 006U)

| Task | Intent |
|------|--------|
| TASK-006V | Legal object promotion persistence + DB idempotency |
| TASK-006W | Promotion worker skeleton (dry-run) |
| TASK-006X | Controlled legal object promotion execution |
| Review | Claude checkpoint after 006X before citation assembly expansion |

## Final principle

Creating canonical legal memory is a governed promotion decision, not an automatic parsing outcome.

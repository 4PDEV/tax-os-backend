# TASK-006Y — Citation Assembly Contract

## Status

**Complete** — governance-only; no persistence or execution

## Objective

Define the governed contract for citation assembly from canonical `legal_object` legal memory.

This task establishes the boundary:

```text
legal_object → citation
```

It does **not** implement citation persistence, workers, execution, retrieval, or answers.

## Canonical contracts

| Artifact | Path |
|----------|------|
| Primary specification (ingestion pipeline) | [`CITATION_ASSEMBLY_CONTRACT.md`](../CITATION_ASSEMBLY_CONTRACT.md) |
| Related assembler governance (004D path) | [`backend/app/services/citation/CITATION_ASSEMBLY_CONTRACT.md`](../backend/app/services/citation/CITATION_ASSEMBLY_CONTRACT.md) |
| Task record | `TASKS/TASK-006Y-CITATION-ASSEMBLY-CONTRACT.md` |

## Prerequisites

- TASK-006U–006X legal object promotion pipeline complete
- TASK-006X1 legal object version identity verified (L-02b)
- Claude review 006U–006X **CLOSED** — **APPROVED FOR CONTINUE** (2026-06-03)
- Citation layer **OPEN**

## Scope delivered

1. Citation role definition (governed reference to canonical legal memory)
2. Citation boundary (`legal_object` → review → `citation`)
3. Eligibility rules for `legal_object` / `legal_object_version`
4. Future `CitationAssemblyRequest` / `CitationAssemblyResult` contracts
5. Citation status and error category taxonomies
6. Idempotency doctrine (`legal_object_version_id` canonical identity)
7. `force_reassembly` doctrine (sole replay bypass)
8. `citation_hash` doctrine (default: `legal_object_version_id`)
9. Provenance chain through citation
10. Temporal no-inference alignment
11. Citation content, answer, and retrieval boundaries
12. OD-021 concurrency carry-forward

## Explicit prohibitions

- no citation persistence tables (006Z)
- no citation workers
- no citation assembly execution
- no retrieval or answer generation
- no legal/tax/applicability/consequence interpretation
- no AI/LLM usage

## Doctrine (critical)

| Concept | Rule |
|---------|------|
| `legal_object` | Canonical legal memory |
| `citation` | Governed reference to that memory |
| Assembly | Governed transition — **not** automatic promotion output |

**`legal_object` ≠ citation · `citation` ≠ answer · `citation` ≠ legal meaning**

## Acceptance criteria

| Criterion | Met |
|-----------|-----|
| Citation assembly contract exists | Yes |
| Request contract defined | Yes |
| Result contract defined | Yes |
| Status values defined | Yes |
| Error categories defined | Yes |
| Identity doctrine documented | Yes |
| Force-reassembly doctrine documented | Yes |
| Provenance doctrine documented | Yes |
| Temporal alignment documented | Yes |
| Answer boundary documented | Yes |
| Retrieval boundary documented | Yes |
| Governance docs updated | Yes |
| No persistence introduced | Yes |
| No execution introduced | Yes |

## Next (not authorized by this task)

| Task | Scope |
|------|-------|
| TASK-006Z | Citation persistence — append-only assembly requests/results |
| TASK-007A+ | Retrieval and query runtime |

Requires explicit governance approval before implementation.

## References

- [LEGAL_OBJECT_PROMOTION_CONTRACT.md](../LEGAL_OBJECT_PROMOTION_CONTRACT.md)
- [CLAUDE_REVIEW_LEGAL_OBJECT_PROMOTION_006U-X.md](../CLAUDE_REVIEW_LEGAL_OBJECT_PROMOTION_006U-X.md)
- [OPEN_DECISIONS.md](../OPEN_DECISIONS.md) (OD-021)

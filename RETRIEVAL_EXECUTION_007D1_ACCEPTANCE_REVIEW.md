# TASK-007D1 Acceptance Review — Retrieval Execution Remediation

**Review type:** Remediation acceptance — authorizes **TASK-007E** controlled retrieval execution scope only  
**Date:** 2026-06-02  
**Closure date:** 2026-06-02  
**Authority:** [`RETRIEVAL_EXECUTION_REMEDIATION_007D1.md`](RETRIEVAL_EXECUTION_REMEDIATION_007D1.md), [`ARCHITECTURE_REVIEW_RETRIEVAL_EXECUTION_007D-PREAUTH.md`](ARCHITECTURE_REVIEW_RETRIEVAL_EXECUTION_007D-PREAUTH.md)

**Verdict:** **CLOSED** — **TASK-007E AUTHORIZED WITH CONDITIONS**

---

## Findings closed

| ID | Finding | Status |
|----|---------|--------|
| RW-01 | `AS_OF_DATE` overlap / ambiguity taxonomy | **CLOSED** |
| RW-02 | Silent latest fallback at execution | **CLOSED** |
| RW-03 | Citation behavior at execution | **CLOSED** |
| RW-04 | Total deterministic ordering | **CLOSED** |
| RW-05 | Execution leakage guards | **CLOSED** |
| RW-06 | Execution staging sequence | **CLOSED** |

---

## Platform state after acceptance

| Layer / capability | Status |
|--------------------|--------|
| Extraction (006M–006P1) | **COMPLETE** |
| Parsing (006Q–006T1A) | **COMPLETE** |
| Legal object layer (006U–006X1) | **COMPLETE** |
| Citation layer (006Y–006AD) | **COMPLETE** |
| Retrieval runtime contract (007B) | **COMPLETE** |
| Retrieval persistence (007C) | **COMPLETE** |
| Retrieval worker skeleton (007D) | **COMPLETE** |
| Retrieval execution design (007D1) | **COMPLETE** |
| **TASK-007E** controlled retrieval execution | **AUTHORIZED FOR IMPLEMENTATION** |
| Ranking | **NOT AUTHORIZED** |
| Answer runtime | **NOT AUTHORIZED** |
| AI / semantic retrieval | **NOT AUTHORIZED** |
| Concurrent retrieval workers (OD-021) | **NOT AUTHORIZED** |

---

## Authorization envelope (TASK-007E — controlled execution only)

**Approved for implementation only:**

| Item | Scope |
|------|--------|
| Pipeline | `retrieval_request` → execution → `retrieval_evidence_references` → `completed` `retrieval_result` |
| Temporal modes | `AS_OF_DATE` (legal-object window), `EXACT_VERSION`, explicit-only `LATEST_VERSION` |
| AS_OF_DATE | `effective_from` / `effective_to` on `legal_object_version` only — no source-version fallback |
| Ambiguity (default) | Return all matching versions — no silent winner |
| No fallback | Empty `AS_OF_DATE` / `EXACT_VERSION` → `completed`+0 — never silent `LATEST_VERSION` |
| Citations | Read-only attach when present; citation-less evidence valid; no `CitationAssembler` |
| Ordering | Total deterministic `ORDER BY` → `deterministic_order_index`; ordering ≠ ranking |
| Persistence | Append-only via `retrieval_persistence`; metadata whitelist (RP-06) |
| Failure | `accepted` → `failed` with explicit `error_category` |
| Zero-result | `completed`, `result_count=0` — not failure, not mode fallback |
| Tests (RW-05) | Import/schema/execution leakage guards |
| OD-021 | Single-worker only |

**Conditions on TASK-007E authorization:**

1. Implementation must conform to [`RETRIEVAL_EXECUTION_REMEDIATION_007D1.md`](RETRIEVAL_EXECUTION_REMEDIATION_007D1.md), [`RETRIEVAL_PERSISTENCE_REMEDIATION_007C1.md`](RETRIEVAL_PERSISTENCE_REMEDIATION_007C1.md), and [`RETRIEVAL_RUNTIME_CONTRACT.md`](RETRIEVAL_RUNTIME_CONTRACT.md).
2. **007D dry-run worker** remains unchanged — controlled mode is additive provider + runner path.
3. Retrieval execution selects evidence — it does **not** rank, answer, or interpret.
4. Ranking, answers, AI retrieval, and concurrent workers remain **not authorized**.

**Explicitly not authorized in TASK-007E:**

- Ranking, relevance scoring, confidence scoring
- Semantic / vector / AI search
- Answer generation, legal reasoning, tax reasoning
- Citation creation or re-assembly
- Concurrent retrieval workers
- HTTP/API routes (unless separate task)

---

## Doctrine chain (unchanged)

```text
parsed_structure ≠ legal object
legal_object ≠ legal meaning
legal_object ≠ citation
citation ≠ retrieval result
retrieval result ≠ answer
retrieval execution ≠ ranking
```

Retrieval execution may select evidence. It may not rank evidence, generate answers, or infer legal meaning.

---

## Governed pipeline (retrieval layer)

```text
TASK-007A  Review
  → TASK-007A1 Remediation → Acceptance
  → TASK-007B  Contract
  → TASK-007C  Pre-Auth → 007C1 → Acceptance → Persistence
  → TASK-007D  Dry-Run Skeleton
  → TASK-007D1 Remediation → Acceptance (this document)
  → TASK-007E  Controlled Retrieval Execution  ← authorized now
  → Retrieval Layer Review                    ← future gate
```

Mirrors citation governance maturity before TASK-006AD implementation.

---

## Next gate

**TASK-007E** — deliver controlled retrieval execution per this authorization envelope.

After 007E acceptance: **Retrieval Layer Review** (not yet open).

---

END OF TASK-007D1 ACCEPTANCE REVIEW

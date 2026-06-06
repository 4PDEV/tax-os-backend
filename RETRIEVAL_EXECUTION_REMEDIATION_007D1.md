# Retrieval Execution Remediation — TASK-007D1

## Purpose

Authoritative remediation specification for future **TASK-007E** controlled retrieval execution, addressing findings from [`ARCHITECTURE_REVIEW_RETRIEVAL_EXECUTION_007D-PREAUTH.md`](ARCHITECTURE_REVIEW_RETRIEVAL_EXECUTION_007D-PREAUTH.md).

**This document modifies planned architecture only.** It does not implement retrieval execution, evidence references, worker modifications, APIs, ranking, answers, or AI search.

| Item | Status |
|------|--------|
| TASK-007D dry-run skeleton | **Complete** — **ACCEPTED** |
| TASK-007D1 remediation package | **Complete** — RW-01 through RW-06 addressed at governance level |
| TASK-007D1 acceptance review | **Pending** — required before TASK-007E authorization |
| TASK-007E controlled execution | **NOT AUTHORIZED** |

---

## Remediation index

| Finding | Severity | Section | Status |
|---------|----------|---------|--------|
| RW-01 | HIGH | `AS_OF_DATE` overlap / ambiguity | **Addressed** |
| RW-02 | HIGH | No silent latest fallback | **Addressed** |
| RW-03 | MEDIUM | Citation behavior at execution | **Addressed** |
| RW-04 | HIGH | Total deterministic ordering | **Addressed** |
| RW-05 | HIGH | Execution leakage guards | **Addressed** |
| RW-06 | LOW | Execution staging sequence | **Addressed** |
| OD-021 | INFO | Concurrent workers | **Addressed** |

---

## RW-01 — `AS_OF_DATE` overlap and ambiguity

### Problem

Multiple `legal_object_versions` may match a requested `as_of_date`. Execution behavior was undefined — risk of silent winner selection.

### Selection doctrine (mandatory)

`AS_OF_DATE` selects `legal_object_versions` whose **legal-object applicability window** contains the requested date:

```text
effective_from <= as_of_date
AND (effective_to IS NULL OR effective_to >= as_of_date)
```

| Source | Use for AS_OF_DATE? |
|--------|---------------------|
| `legal_object_version.effective_from` | **Yes** |
| `legal_object_version.effective_to` | **Yes** |
| `source_version.effective_from` / `effective_to` | **No** — metadata only |
| TASK-004E-style fallback | **Prohibited** |

### Ambiguity behavior (governed — preferred)

**Preferred (default for TASK-007E):** Return **all** matching versions as evidence references — one row per match, each version-pinned. No silent winner.

| Rule | Requirement |
|------|-------------|
| Multiple matches | Persist all matches with distinct `deterministic_order_index` values |
| Silent selection | **Prohibited** — no arbitrary `.first()` without explicit ordering |
| Arbitrary winner | **Prohibited** |

### Alternative ambiguity path (operator-configurable — future)

If request envelope includes `ambiguity_policy=fail_on_overlap` (future 007E flag):

- On multiple matches → `retrieval_status=failed`
- `error_category=temporal_ambiguity` (planned CHECK extension for 007E)
- Explicit `error_message` listing matched `legal_object_version_id` values

**Default:** `ambiguity_policy=return_all_matches` — no failure on overlap.

### Prohibited

- Silent winner selection
- Implicit deduplication without documented rule
- Source-version date substitution

---

## RW-02 — No silent latest fallback

### Problem

Empty results from `AS_OF_DATE` or `EXACT_VERSION` could silently degrade to `LATEST_VERSION` — violating explicit temporal doctrine (R-01).

### Governed rules (mandatory)

| Scenario | Behavior | Prohibited |
|----------|----------|------------|
| `AS_OF_DATE` — zero matches | `completed`, `result_count=0` | Fallback to `LATEST_VERSION` |
| `EXACT_VERSION` — version not found / not in scope | `failed` or `completed`+0 per pin validation | Fallback to `LATEST_VERSION` |
| `LATEST_VERSION` — no current pointer | `failed` (`version_missing`) or `completed`+0 | Silent substitute version |

**Only** `retrieval_mode=LATEST_VERSION` may use `legal_objects.current_version_id` or equivalent latest pointer — and only when mode is explicit on the request.

### Zero-result semantics (unchanged from RP-07)

```text
retrieval_status = completed
result_count = 0
```

Means **successful empty retrieval** — not failure, not answer absence, not legal conclusion.

Empty result is **not** a trigger for mode fallback.

---

## RW-03 — Citation behavior at execution

### Doctrine

Citation-less evidence is **valid**. Execution must not require citation presence for every evidence row.

### When citation exists (read-only lookup)

Attach on evidence reference:

- `citation_id`
- `citation_hash`

Validation per [`RETRIEVAL_PERSISTENCE_REMEDIATION_007C1.md`](RETRIEVAL_PERSISTENCE_REMEDIATION_007C1.md) RP-03 — provenance pins must match.

### When citation does not exist

Persist evidence reference **without** `citation_id` / `citation_hash`. Legal-object version pin alone is valid evidence.

### Prohibited at execution

- Create citation rows
- Invoke `CitationAssembler` / TASK-004D
- Reassemble or re-render citation text during retrieval
- Infer applicability from citation presence or absence

```text
retrieval execution ≠ citation assembly
```

---

## RW-04 — Total deterministic ordering

### Problem

Execution ordering must terminate in a **unique** total order before `deterministic_order_index` assignment.

### Canonical sort keys (007E — mandatory `ORDER BY` chain)

Apply in sequence; each key must be declared:

| Priority | Sort key | Direction |
|----------|----------|-----------|
| 1 | `legal_object_version.effective_from` | ASC |
| 2 | `legal_object_id` | ASC |
| 3 | `legal_object_version_id` | ASC |
| 4 | `citation_hash` | ASC NULLS LAST |
| 5 | `object_identifier` | ASC NULLS LAST |

Equivalent tie-break material may be used if documented — must produce **identical** order across replays.

### `deterministic_order_index` assignment

1. Apply full `ORDER BY` chain to candidate evidence set.
2. Assign index starting at **1**, incrementing by 1 per row.
3. Persist via `UNIQUE(retrieval_result_id, deterministic_order_index)` (RP-05).

```text
deterministic_order_index ≠ ranking
ordering ≠ relevance
```

### Prohibited ordering keys

- `relevance_score`
- `ranking_score`
- `confidence_score`
- `semantic_score`
- `RANDOM()`
- implicit database row order
- `LIMIT 1` without prior deterministic sort (selection ambiguity)

---

## RW-05 — Execution leakage guards

### Future tests (TASK-007E — mandatory)

#### Import guards

Execution package must **not** import:

- answer runtime modules
- ranking runtime modules
- AI / LLM client libraries
- semantic / vector search modules
- `CitationAssembler` / TASK-004D assembler

#### Schema guards

- No answer columns on retrieval tables
- No ranking columns on retrieval tables
- `evidence_metadata` whitelist enforced (RP-06)

#### Execution guards

| Prohibited pattern | Test method |
|--------------------|-------------|
| `LIMIT` used as ranking proxy | Static analysis + integration |
| `ORDER BY` relevance/confidence/semantic | Static analysis |
| `deterministic_order_index` interpreted as rank | Unit test on documentation/API |
| Answer text in evidence payloads | Insert rejection test |

Extend RP-08 mechanical tests for execution scope.

---

## RW-06 — Execution staging sequence

### Approved governed sequence

```text
TASK-007D   Dry-run worker skeleton        ← COMPLETE / ACCEPTED
  → TASK-007D1  Remediation package        ← this document
  → TASK-007D1  Acceptance review          ← pending
  → TASK-007E   Controlled retrieval execution  ← NOT AUTHORIZED
  → Retrieval layer review                 ← future gate
```

**TASK-007E is the first task authorized to select evidence and create `retrieval_evidence_references`.**

TASK-007D must remain dry-run only (`accepted` → `skipped`). TASK-007D worker code is **not modified** by 007D1.

---

## OD-021 — Concurrent workers (carry-forward)

| Item | Rule |
|------|------|
| Current mode | **Single-worker only** |
| Concurrent retrieval workers | **NOT AUTHORIZED** |
| Future requirement | `request_hash`-keyed advisory or row locks before concurrency gate |
| 007E scope | No locking implementation unless separate authorization |

---

## Planned TASK-007E controlled execution flow

### Success with evidence

```text
retrieval_request
  → retrieval_result (accepted)
  → retrieval execution (version selection + citation lookup read-only)
  → retrieval_evidence_references (N rows, ordered)
  → retrieval_result (completed, result_count=N)
```

### Success — zero results

```text
retrieval_request
  → retrieval_result (accepted)
  → retrieval execution (no matches)
  → retrieval_result (completed, result_count=0)
```

No evidence rows. **Not** failure. **Not** mode fallback.

### Failure

```text
retrieval_request
  → retrieval_result (accepted)
  → retrieval_result (failed, error_category, error_message)
```

On citation provenance mismatch: `error_category=provenance_incomplete` per RP-03.

On configured ambiguity fail: `error_category=temporal_ambiguity`.

### Dry-run (007D — unchanged)

```text
retrieval_request
  → retrieval_result (accepted)
  → dry-run provider
  → retrieval_result (skipped, result_count=0)
```

**`completed` is not produced by 007D dry-run.**

---

## Planned error category extension (007E only)

When `ambiguity_policy=fail_on_overlap` is implemented:

```sql
-- extend ck_retrieval_result_error_category to include:
'temporal_ambiguity'
```

Default 007C CHECK set unchanged until 007E migration.

---

## Authorization gate (TASK-007E)

TASK-007E may be authorized only after:

1. TASK-007D dry-run skeleton accepted — **done**
2. TASK-007D1 remediation package accepted — **pending acceptance review**
3. Bounded TASK-007E implementation spec derived from this document

Ranking, answers, AI retrieval, and concurrent workers remain **not authorized**.

---

## References

- [`ARCHITECTURE_REVIEW_RETRIEVAL_EXECUTION_007D-PREAUTH.md`](ARCHITECTURE_REVIEW_RETRIEVAL_EXECUTION_007D-PREAUTH.md)
- [`RETRIEVAL_RUNTIME_CONTRACT.md`](RETRIEVAL_RUNTIME_CONTRACT.md)
- [`RETRIEVAL_PERSISTENCE_REMEDIATION_007C1.md`](RETRIEVAL_PERSISTENCE_REMEDIATION_007C1.md)
- [`TASKS/TASK-007D-RETRIEVAL-WORKER-SKELETON.md`](TASKS/TASK-007D-RETRIEVAL-WORKER-SKELETON.md)

---

## Acceptance criteria (007D1)

- [x] RW-01 through RW-05 addressed
- [x] RW-03, RW-06 clarified
- [x] OD-021 carried forward
- [x] Planned 007E flow documented
- [x] No implementation introduced
- [x] TASK-007E remains NOT AUTHORIZED

---

END OF RETRIEVAL EXECUTION REMEDIATION 007D1

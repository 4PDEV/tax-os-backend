# Ranking Runtime Remediation — TASK-008A1

## Purpose

Authoritative remediation specification for future **TASK-008B** ranking runtime contract, addressing findings **RK-01 through RK-11** from TASK-008A Ranking Runtime Pre-Authorization Review.

**This document modifies planned architecture only.** It does not implement ranking, persistence tables, migrations, models, workers, APIs, answers, or AI search.

| Item | Status |
|------|--------|
| TASK-008A pre-auth review | **Complete** — APPROVED WITH REQUIRED REMEDIATION BEFORE 008B |
| TASK-008A1 remediation package | **Complete** — RK-01 through RK-11 addressed at governance level |
| TASK-008A1 acceptance review | **Closed** — [`RANKING_RUNTIME_008A1_ACCEPTANCE_REVIEW.md`](RANKING_RUNTIME_008A1_ACCEPTANCE_REVIEW.md) |
| TASK-008B contract | **AUTHORIZED WITH CONDITIONS** |
| TASK-008C / 008D | **NOT AUTHORIZED** |
| Answer runtime (009A) | **NOT AUTHORIZED** |

---

## RK-01 — Layer boundary: separate ranking vs retrieval ordering profiles

### Problem (blocking)

TASK-008A identified ambiguity between:

- **Option A:** a distinct governed ranking layer (`retrieval_result` → `ranking_request` → `ranking_result` → `ranked_evidence_reference`)
- **Option B:** deterministic **ordering profiles** inside retrieval (`CANONICAL`, `EFFECTIVE_DATE_DESC`, `GROUP_BY_SOURCE`, `GROUP_BY_DOCUMENT`)

Retrieval (007E) already performs **evidence selection** and assigns **`deterministic_order_index`** under a single canonical `ORDER BY` chain. Without a clear boundary, future work may:

- relabel relevance ranking as “ordering profiles,” or
- duplicate persistence lifecycle inside retrieval, eroding `retrieval result ≠ ranking`.

### Required analysis

#### Option A — Separate ranking layer

| Dimension | Assessment |
|-----------|------------|
| **Doctrine impact** | **Strong.** Preserves architecture chain: Evidence → Ranking → Answer Assembly → Response Runtime. `retrieval result ≠ ranking` remains structurally enforceable. Retrieval owns selection + default canonical order; ranking owns **presentation permutations only**. |
| **Provenance impact** | **Strong.** `retrieval_evidence_reference` rows are immutable inputs. `ranked_evidence_reference` rows point back to source evidence row IDs + `retrieval_result_id` — no mutation of legal pins. |
| **Persistence impact** | **Moderate.** New append-only tables: `ranking_requests`, `ranking_results`, `ranked_evidence_references`. Additional lifecycle rows per profile replay. |
| **Auditability** | **Strong.** Operators can answer: “what was retrieved?” vs “in what presentation order was it shown?” Separate `request_hash` namespaces. |
| **Complexity** | **Moderate.** Mirrors proven 007C/007E pattern; one more worker skeleton + controlled execution gate. |
| **Future creep risk** | **Lower** if bounded. Separate layer makes relevance/AI additions visible and blockable at ranking pre-auth. Risk remains if `ranking_profile` enum grows ungoverned — mitigated by mechanical-profile whitelist (§RK-08). |

#### Option B — Retrieval ordering profiles

| Dimension | Assessment |
|-----------|------------|
| **Doctrine impact** | **Weak.** `GROUP_BY_SOURCE` / `EFFECTIVE_DATE_DESC` are mechanically reordering — but live **inside** retrieval, collapsing `retrieval result ≠ ranking`. Answer assembly would consume a “retrieval result” that is already reordered without ranking lifecycle. |
| **Provenance impact** | **Mixed.** Same evidence rows could gain multiple order indices or require re-execution per profile — blurs immutability of retrieval output. |
| **Persistence impact** | **Lower short-term.** Extends `retrieval_requests` envelope with `ordering_profile` — but forces `request_hash` to encode profile, multiplying retrieval rows for the same evidence set. |
| **Auditability** | **Weaker.** Harder to distinguish “evidence set produced” from “presentation order applied” in one result row. |
| **Complexity** | **Lower short-term.** No new tables — but retrieval execution scope expands, violating 007E closure boundary. |
| **Future creep risk** | **High.** `ordering_profile=SEMANTIC_SIMILARITY` or `RELEVANCE_DESC` is a one-enum addition away. Profile namespace conflates selection, canonical order, and presentation order. |

### Decision (RK-01)

**Recommendation: Option A — retain a distinct governed ranking layer.**

**Rationale:**

1. **Spec is law:** Platform architecture chain explicitly places **Ranking** between Evidence and Answer Assembly. Option B folds ranking into retrieval and breaks that chain at the persistence boundary.
2. **Doctrine is law:** Retrieval (007E) is **closed**. Its `deterministic_order_index` is the canonical mechanical order for the evidence set — explicitly **not a rank**. Presentation reordering belongs in a separate lifecycle.
3. **Permutation-only semantics** (RK-04) are easier to enforce when ranking consumes a **completed** `retrieval_result` and emits `ranked_evidence_reference` rows that reference existing evidence — no re-selection, no drops, no adds.
4. **Mechanical profiles** (`CANONICAL`, `EFFECTIVE_DATE_DESC`, `GROUP_BY_SOURCE`, `GROUP_BY_DOCUMENT`) are **authorized only as ranking profiles** — deterministic `ORDER BY` declarations, not relevance.

**Retrieval layer remains unchanged.** Ranking does not modify `retrieval_evidence_references` or `retrieval_results`.

**Option B rejected** for production architecture. Ordering-profile convenience does not outweigh doctrine erosion and AI/relevance creep risk.

---

## Remediation index

| Finding | Severity | Section | Status |
|---------|----------|---------|--------|
| RK-01 | HIGH | Layer boundary — Option A vs B | **Addressed (§RK-01)** — **Option A** |
| RK-02 | HIGH | `ranking_request_hash` identity | **Addressed (§RK-02)** |
| RK-03 | HIGH | `completed` `retrieval_result` prerequisite | **Addressed (§RK-03)** |
| RK-04 | HIGH | Permutation invariant | **Addressed (§RK-04)** |
| RK-05 | HIGH | Read-only provenance | **Addressed (§RK-05)** |
| RK-06 | HIGH | Append-only persistence | **Addressed (§RK-06)** |
| RK-07 | HIGH | No score columns | **Addressed (§RK-07)** |
| RK-08 | HIGH | No relevance / semantic / AI inputs | **Addressed (§RK-08)** |
| RK-09 | HIGH | No answer generation | **Addressed (§RK-09)** |
| RK-10 | MEDIUM | Mechanical leakage guards | **Addressed (§RK-10)** |
| RK-11 | INFO | OD-021 concurrent workers | **Addressed (§RK-11)** |

---

## RK-02 — `ranking_request_hash` identity

### Problem

Ranking requests lack a governed identity formula separate from retrieval `request_hash` and evidence row identity.

### Required doctrine

```text
ranking_request_hash = SHA-256(canonical_json(normalized_ranking_envelope))
```

**Normalized envelope includes (minimum):**

| Field | Inclusion |
|-------|-----------|
| `retrieval_result_id` | Required — pins input evidence set |
| `ranking_profile` | Required — mechanical profile enum (§RK-08) |
| `contract_version` | Optional schema generation tag |

**Excluded from hash:**

- raw `query_text`
- actor fields, timestamps, notes
- relevance parameters (prohibited)

**Rules:** Same canonical JSON rules as RP-01 / 007C1 (lexicographic keys, compact UTF-8, ISO dates, no floats).

**Separation:**

```text
request_hash (retrieval) ≠ ranking_request_hash ≠ evidence row identity
```

Idempotency: default duplicate `ranking_request_hash` returns existing lifecycle row. `force_replay` creates new append-only rows (006Z / 007C precedent).

---

## RK-03 — Completed `retrieval_result` prerequisite

### Problem

Ranking could run against `accepted` or `failed` retrieval rows, or against in-flight execution — producing unordered evidence or bypassing retrieval doctrine.

### Required doctrine

Ranking may start **only** when:

| Prerequisite | Rule |
|--------------|------|
| `retrieval_result.retrieval_status` | Must be `completed` |
| `retrieval_result.result_count` | Must equal count of `retrieval_evidence_references` for that result |
| Zero-result | `result_count=0` is valid — ranking produces empty ranked set (completed, `rank_count=0`) |
| Dry-run `skipped` | **Prohibited** input — no evidence references |
| `failed` retrieval | **Prohibited** input |

Ranking request must carry `retrieval_result_id` FK. Service validates status before execution.

---

## RK-04 — Permutation invariant

### Problem

“Ranking” could be implemented as subset selection, top-K truncation, or deduplication — introducing relevance-like behavior.

### Required doctrine

Ranking is **permutation only** over the input evidence multiset.

| Rule | Requirement |
|------|-------------|
| Input count | `N` = `retrieval_result.result_count` |
| Output count | `rank_count` must equal `N` (or 0 when N=0) |
| Set equality | Every input `retrieval_evidence_reference_id` appears exactly once in ranked output |
| No adds | Ranking must not introduce evidence not in retrieval result |
| No drops | No `LIMIT`-as-ranking; no “top K” unless K=N |
| No dedup | Duplicates in retrieval (if any) preserve multiplicity |

**Index naming:** `presentation_order_index` (or `rank_position`) — **not** `relevance_rank`. Must not reuse `deterministic_order_index` (retrieval-owned).

**Profile `CANONICAL`:** Permutation that preserves retrieval `deterministic_order_index` order (identity permutation).

---

## RK-05 — Read-only provenance

### Problem

Ranked output could mutate `legal_object_version_id`, `citation_id`, or source pins — breaking audit chain to `source_version`.

### Required doctrine

Each `ranked_evidence_reference` must:

| Field | Rule |
|-------|------|
| `retrieval_result_id` | Required — membership scope |
| `retrieval_evidence_reference_id` | Required FK — primary lineage |
| `presentation_order_index` | Ranking-owned order only |

**Prohibited on ranked rows:** copying `legal_object_id`, `legal_object_version_id`, `source_version_id`, `citation_id`, `citation_hash`, or any provenance denormalization.

Provenance obtained **exclusively** via join to `retrieval_evidence_references`.

**Prohibited during ranking:**

- Re-querying legal object tables for “better” version
- Citation creation or `CitationAssembler`
- Temporal re-filtering
- Provenance “correction” or inference
- Copying provenance fields onto ranked output rows

---

## RK-06 — Append-only persistence

### Problem

No governed persistence doctrine for ranking lifecycle.

### Required doctrine (planned — 008C)

Append-only tables (names indicative):

| Table | Role |
|-------|------|
| `ranking_requests` | Governed request envelope + `ranking_request_hash` |
| `ranking_results` | Lifecycle (`accepted` → `completed` / `failed` / dry-run `skipped`) |
| `ranked_evidence_references` | Permutation output rows |

**Rules:**

- No `UPDATE` of prior ranking results or ranked references
- No `DELETE` of prior rows
- `force_replay` appends new lifecycle rows
- `ranking_result` stores `rank_count` — must equal persisted ranked reference count

Mirror 007C RP-01–RP-08 discipline adapted for ranking (metadata whitelist in 008C remediation if needed).

---

## RK-07 — No score columns

### Problem

Schema or DTO drift could add `relevance_score`, `confidence_score`, `semantic_score`, `ranking_score`.

### Required doctrine

**Prohibited columns / fields (DB, models, API, tests):**

- `relevance_score`
- `confidence_score`
- `semantic_score`
- `ranking_score`
- `ai_score`
- `llm_score`
- `bm25_score`
- `embedding_distance`
- any float metric implying preference or legal weight

**Permitted:**

- `presentation_order_index` (integer, 1..N)
- `ranking_profile` (enum)
- mechanical `sort_key` metadata on whitelist only (008C)

```text
presentation_order_index ≠ relevance rank
```

---

## RK-08 — No relevance / semantic / AI inputs

### Problem

Ranking request envelope could admit `query_text`, embeddings, model IDs, or “sort by relevance.”

### Required doctrine

**Permitted `ranking_profile` values (mechanical only — initial whitelist):**

| Profile | Behavior |
|---------|----------|
| `CANONICAL` | Identity permutation — retrieval `deterministic_order_index` order |
| `EFFECTIVE_DATE_DESC` | `effective_from DESC NULLS LAST`, then canonical tie-breakers |
| `GROUP_BY_SOURCE` | Group by `source_version_id`, canonical order within group |
| `GROUP_BY_DOCUMENT` | Group by `source_document_id`, canonical order within group |

**Prohibited inputs:**

- `query_text` as ranking driver
- semantic / vector / embedding fields
- AI / LLM model parameters
- `relevance_mode`, `similarity_threshold`, `top_k` (when K < N)
- external corpus or web retrieval

New profiles require governance amendment — not runtime configuration drift.

---

## RK-09 — No answer generation

### Problem

Ranking output could include synthesized text, conclusions, or applicability flags for downstream “convenience.”

### Required doctrine

Ranking returns **ordered evidence reference pointers only**.

**Prohibited output fields:**

- `answer_text`
- `legal_conclusion`
- `applicability_flag`
- `recommendation_text`
- `summary_text`
- `interpretive_notes`

```text
ranking ≠ answer
answer ≠ legal conclusion
```

Answer assembly remains **009A+** — not authorized.

---

## RK-10 — Mechanical leakage guards

### Problem

Ranking execution path could import answer, AI, semantic, or retrieval re-execution modules.

### Required doctrine (planned tests — 008D)

**Import guards (mandatory):**

- `app.services.answer`
- `app.services.ai`
- `app.services.semantic`
- `app.services.vector`
- `app.services.retrieval_execution` (re-selection prohibited)
- `CitationAssembler` / `app.services.citation.assembler`

**Schema / output guards:**

- Scan ranking models and result DTOs for prohibited fields (§RK-07, §RK-09)
- Assert `rank_count == len(ranked_evidence_references)`
- Assert permutation invariant (§RK-04)

**LIMIT guard:** Any `LIMIT` in ranking SQL must equal input evidence count or be rejected at review time.

---

## RK-11 — OD-021 single-worker constraint

### Problem

Concurrent ranking workers could race on `ranking_request_hash` or duplicate permutations.

### Required doctrine

| Rule | Status |
|------|--------|
| Single-worker ranking execution | **Acceptable on `main`** (OD-021 carry-forward) |
| Concurrent ranking workers | **NOT AUTHORIZED** |
| Future concurrency | `ranking_request_hash`-keyed advisory or row locks before concurrency gate |

008D worker skeleton must reject concurrent execution modes unless separately authorized.

---

## Planned ranking pipeline (post-008A1 acceptance)

```text
retrieval_result (completed)
  → ranking_request (ranking_request_hash)
  → ranking_result (accepted)
  → [dry-run: skipped | controlled: permutation]
  → ranked_evidence_references (presentation_order_index)
  → ranking_result (completed, rank_count=N)
```

**Dry-run terminal:** `skipped` (`rank_count=0`) — no ranked references.

**Controlled success:** `accepted` → `completed`.

**Failure:** `accepted` → `failed` with explicit `error_category`.

---

## Authorization gate (TASK-008B)

TASK-008B may be authorized only after:

1. TASK-008A pre-auth review — **done**
2. TASK-008A1 remediation package — **this document**
3. TASK-008A1 acceptance review **CLOSED**

Ranking persistence (008C), worker (008D), and execution remain **not authorized** until respective gates close.

Answer runtime (009A) remains **not authorized** until ranking layer review closes.

---

## Acceptance criteria (008A1)

- [x] RK-01 resolved — **Option A** with explicit rationale
- [x] RK-02 through RK-11 addressed at spec level
- [x] Permutation invariant documented
- [x] Mechanical profile whitelist documented
- [x] No implementation introduced
- [x] TASK-008A1 acceptance review **CLOSED** — TASK-008B authorized with conditions

---

END OF RANKING RUNTIME REMEDIATION 008A1

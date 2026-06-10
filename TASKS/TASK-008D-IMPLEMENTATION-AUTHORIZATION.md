# TASK-008D — Implementation Authorization Package

## Status

**COMPLETE** — implementation design locked for bounded authorization prompt.

**TASK-008D implementation remains NOT AUTHORIZED** until explicit acceptance of this package (or amended prompt).

| Phase | Status |
|-------|--------|
| TASK-008D-PREAUTH | **ACCEPTED** — `bf201f2` |
| TASK-008D-IMPLEMENTATION-AUTHORIZATION (this document) | **COMPLETE** — design package |
| TASK-008D controlled execution code | **NOT AUTHORIZED** |
| TASK-008D worker skeleton | **NOT AUTHORIZED** |

## Accepted baseline

| Item | Value |
|------|--------|
| HEAD | `bf201f2` |
| TASK-008C | **COMPLETE** / **ACCEPTED** — Alembic `a8c1e4f92b37` |
| TASK-008D-PREAUTH | **ACCEPTED** |
| DEC-010, DEC-011, DEC-012 | **LOCKED** |
| OD-021 | **LOCKED** — single-worker |

## Binding upstream artifacts

- [`RANKING_RUNTIME_CONTRACT.md`](../RANKING_RUNTIME_CONTRACT.md) (008B-v2)
- [`RANKING_EXECUTION_CONTRACT.md`](../RANKING_EXECUTION_CONTRACT.md)
- [`TASKS/TASK-008C-RANKING-PERSISTENCE.md`](TASK-008C-RANKING-PERSISTENCE.md)
- [`DECISION_LOG.md`](../DECISION_LOG.md) — DEC-010, DEC-011, DEC-012

## Important

This package **does NOT implement** execution services, workers, APIs, tests, models, migrations, or runtime code.

---

## 1. Execution service boundary

### Service name (locked)

```text
backend/app/services/ranking_execution/
```

Primary orchestration entry (locked name):

```text
execute_controlled_ranking(session, *, retrieval_result_id, ranking_profile, ...)
```

Package modules (implementation phase only — not created by this task):

| Module | Responsibility |
|--------|----------------|
| `execution.py` | Orchestration — validate → permute → validate → persist lifecycle |
| `ordering.py` | Profile-specific deterministic sort functions |
| `validation.py` | Pre-execution and post-sort permutation checks |
| `models.py` | In-memory execution DTOs only (not ORM) |

### Responsibilities (execution **must**)

1. Load **completed** `retrieval_result` and all `retrieval_evidence_references` for `retrieval_result_id` (read-only)
2. Validate prerequisites and count integrity before permutation
3. Resolve sort-time read fields (per §3) via permitted read-only joins — **not persisted** on ranked rows
4. Apply declared `ranking_profile` mechanical permutation deterministically
5. Run permutation integrity validation (§4)
6. Persist lifecycle through **008C only** — `create_ranking_request`, `create_ranking_result`, `create_ranked_evidence_reference`
7. Map failures to canonical `error_category` values (§8)

### Non-responsibilities (execution **must NOT**)

| Prohibited | Rationale |
|------------|-----------|
| Re-run retrieval / invoke `retrieval_execution` | DEC-012 — selection is closed |
| Generate answers | `ranking` ≠ answer |
| Generate citations / invoke `CitationAssembler` | Provenance lives once (DEC-010) |
| Semantic / vector / AI ranking | Not authorized |
| Relevance scoring or interpretive weights | RK-07 / RK-09 |
| Legal conclusions or applicability | Not authorized |
| Direct SQL writes / ORM mutation of historical ranking rows | Append-only 008C |
| Runtime-defined profiles | Closed enum only |
| Concurrent worker orchestration | OD-021 |

---

## 2. Execution inputs

### Required inputs (locked)

| Input | Type | Rule |
|-------|------|------|
| `retrieval_result_id` | UUID | Must reference existing `retrieval_results.id` |
| `ranking_profile` | enum | One of `CANONICAL`, `EFFECTIVE_DATE_DESC`, `GROUP_BY_SOURCE`, `GROUP_BY_DOCUMENT` |
| `contract_version` | str | Default `008B-v2` (`CURRENT_CONTRACT_VERSION` from `ranking_persistence`) |
| `force_replay` | bool | Default `false` |
| `replay_nonce` | str \| None | Required entropy source when `force_replay=true` (DEC-011) |

### Optional envelope inputs (do not affect permutation)

| Input | Notes |
|-------|-------|
| `requested_by_actor_type` | Persistence metadata only |
| `requested_by_actor_identifier` | Persistence metadata only |
| `notes` | Persistence metadata only |

Excluded from `ranking_request_hash` and sort: actor fields, timestamps, notes, query text, scores.

### Pre-execution validation sequence (locked)

Execute in order; abort with mapped `error_category` on failure:

| Step | Check | Failure category |
|------|-------|------------------|
| V-01 | `ranking_profile` in closed enum | `profile_not_allowed` |
| V-02 | `retrieval_result` row exists | `retrieval_result_missing` |
| V-03 | `retrieval_status == completed` | `retrieval_result_not_completed` |
| V-04 | `result_count` is not null | `retrieval_result_not_completed` |
| V-05 | Count of `retrieval_evidence_references` for `retrieval_result_id` equals `result_count` | `evidence_reference_missing` |
| V-06 | Each evidence row has resolvable provenance for sort-time reads (§3 joins) | `provenance_incomplete` |
| V-07 | If `force_replay=false`: no existing default `ranking_request` for computed hash | `duplicate_ranking` (or reject at `create_ranking_request`) |
| V-08 | No in-flight `accepted` ranking_result for same default hash (single-worker guard — §9) | `duplicate_ranking` |

After V-01–V-08 pass: persist `ranking_request` + `ranking_result(accepted)`, then execute permutation.

---

## 3. Deterministic ordering algorithms

Sort-time reads permitted from `retrieval_evidence_references` and **read-only** join to `legal_object_versions` on `legal_object_version_id` for `effective_from` only. Values **must not** be copied to `ranked_evidence_references`.

### Shared tie-break chain (after profile primary keys)

Apply mechanically when profile does not already use a key:

```text
1. effective_from ASC NULLS LAST        (omit step 1 when effective_from is primary DESC)
2. legal_object_id ASC
3. legal_object_version_id ASC
4. citation_hash ASC NULLS LAST
5. object_identifier ASC NULLS LAST
6. retrieval_evidence_reference_id ASC  (final unique tiebreaker)
```

**NULLS LAST encoding (locked):** null keys sort after non-null (mirror `retrieval_execution/ordering.py` tuple discipline).

### `CANONICAL`

**Primary key (only):**

```text
deterministic_order_index ASC
```

No tie-break chain required — index is unique per `retrieval_result_id`.

**Output:** identity permutation relative to retrieval order.

### `EFFECTIVE_DATE_DESC`

**Primary:**

```text
effective_from DESC NULLS LAST   (from legal_object_versions join)
```

**Then tie-break (steps 2–6 of shared chain):**

```text
legal_object_id ASC
legal_object_version_id ASC
citation_hash ASC NULLS LAST
object_identifier ASC NULLS LAST
retrieval_evidence_reference_id ASC
```

### `GROUP_BY_SOURCE`

**Step A — group:** `source_version_id` from evidence row.

**Step B — inter-group order:**

```text
source_version_id ASC
```

**Step C — within-group order (shared chain steps 1–6):**

```text
effective_from ASC NULLS LAST
legal_object_id ASC
legal_object_version_id ASC
citation_hash ASC NULLS LAST
object_identifier ASC NULLS LAST
retrieval_evidence_reference_id ASC
```

**Step D — output construction:** stable sort: primary `source_version_id ASC`, secondary within-group chain. Assign `presentation_order_index` 1..N on flattened list.

### `GROUP_BY_DOCUMENT`

**Step A — group:** `source_document_id` from evidence row (nullable).

**Step B — inter-group order:**

```text
source_document_id ASC NULLS LAST
```

NULL `source_document_id` rows form one trailing group.

**Step C — within-group order:** same as `GROUP_BY_SOURCE` within-group chain.

**Step D — output construction:** non-null document groups in `source_document_id ASC` order, then NULL group last; assign `presentation_order_index` 1..N globally.

**No runtime discretion.** Profile choice is the only variable sort behavior.

---

## 4. Permutation validation

### Post-sort validation sequence (locked)

| Step | Check | Failure category |
|------|-------|------------------|
| P-01 | `len(output_ids) == N` where `N = result_count` | `permutation_mismatch` |
| P-02 | `len(output_ids) == len(input_ids)` | `permutation_mismatch` |
| P-03 | `Counter(output_ids) == Counter(input_ids)` (identical multiset) | `permutation_mismatch` |
| P-04 | `set(output_ids) == set(input_ids)` | `permutation_mismatch` |
| P-05 | No ID in output that was not in input (**unexpected evidence**) | `permutation_mismatch` |
| P-06 | No input ID missing from output (**missing evidence**) | `permutation_mismatch` |
| P-07 | `presentation_order_index` assigned 1..N contiguous with no gaps or duplicates | `permutation_mismatch` |
| P-08 | No duplicate `(ranking_result_id, presentation_order_index)` before persist | DB + pre-check |
| P-09 | No duplicate `(ranking_result_id, retrieval_evidence_reference_id)` before persist | DB + pre-check |

### Duplicate / missing / unexpected detection (locked definitions)

| Term | Detection rule |
|------|----------------|
| **Missing evidence** | ∃ id ∈ input multiset where count_output(id) < count_input(id) |
| **Unexpected evidence** | ∃ id ∈ output multiset where count_input(id) < count_output(id) |
| **Duplicate slot** | Two rows assigned same `presentation_order_index` |
| **Duplicate evidence rank** | Same `retrieval_evidence_reference_id` appears twice in output order when input had multiplicity 1 — allowed only when input multiplicity > 1 |

Input evidence IDs loaded from `retrieval_evidence_references` where `retrieval_result_id` matches — no subset selection.

---

## 5. Zero-evidence execution

**Precondition:** `retrieval_status=completed` AND `result_count=0` AND evidence row count = 0.

**Locked path:**

```text
1. Pass pre-execution validation (V-01–V-08)
2. create_ranking_request(...)
3. create_ranking_result(..., ranking_status=accepted)
4. Skip permutation (empty input)
5. Skip create_ranked_evidence_reference (no rows)
6. create_ranking_result(..., ranking_status=completed, rank_count=0, completed_at=now)
```

| Outcome | Value |
|---------|-------|
| `ranking_status` | `completed` |
| `rank_count` | `0` |
| `ranked_evidence_references` rows | `0` |
| `error_category` | `null` |

**Prohibited:** `evidence_set_empty`, `failed` status, or any error for valid zero-result retrieval.

---

## 6. Persistence integration (008C)

### Write boundary (locked — only these functions)

From `app.services.ranking_persistence`:

```python
create_ranking_request(...)
create_ranking_result(...)
create_ranked_evidence_reference(...)
```

**Prohibited writes:** direct SQL, raw `session.add` on ranking ORM models outside persistence module, `UPDATE`/`DELETE` on ranking tables, any mutation helpers.

### Read boundary (allowed — read-only)

| Function | Package | Purpose |
|----------|---------|---------|
| `get_result` | `retrieval_persistence` | Load `retrieval_result` |
| `list_evidence_references` | `retrieval_persistence` | Load input evidence set |
| `find_existing_default_request` | `ranking_persistence` | Idempotency check |
| `list_results_for_request` | `ranking_persistence` | Lifecycle inspection |
| `get_ranking_result` | `ranking_persistence` | Result lookup |
| `list_ranked_evidence_references` | `ranking_persistence` | Post-persist verification (tests) |

Read-only ORM loads for `legal_object_versions.effective_from` join permitted; no writes to retrieval tables.

### Persist sequence (N > 0)

```text
create_ranking_request
→ create_ranking_result(accepted)
→ [permutation]
→ create_ranked_evidence_reference × N
→ create_ranking_result(completed, rank_count=N)
```

On failure after `accepted`: append `create_ranking_result(failed, error_category=..., error_message=...)`.

---

## 7. Replay / idempotency (DEC-011)

### Normal execution (`force_replay=false`)

| Rule | Behavior |
|------|----------|
| Hash envelope | `{retrieval_result_id, ranking_profile, contract_version}` only |
| De-duplication | Partial unique `UNIQUE (ranking_request_hash) WHERE force_replay = false` |
| Duplicate default request | `create_ranking_request` raises / maps to `duplicate_ranking` or `duplicate_rejected` result |
| Determinism | Same retrieval + profile + contract version → same permutation |

### Force replay (`force_replay=true`)

| Rule | Behavior |
|------|----------|
| Hash envelope | Adds `force_replay: true` and `replay_nonce` (DEC-011) |
| Purpose | Additional append-only lifecycle row only |
| Does not bypass | Prerequisite validation, permutation validation, pure-pointer shape |
| Does not alter | Sort output for same evidence set + profile |

### Idempotency outcomes (locked)

| Scenario | Terminal behavior |
|----------|-------------------|
| First default request | Execute and complete (or fail with canonical error) |
| Repeat default request same hash | Reject — `duplicate_ranking` / `duplicate_rejected`; no re-execution |
| Force replay with new nonce | New request row; full validation + execution allowed |

---

## 8. Failure mapping

**Canonical categories only** — no new categories.

| Execution condition | `error_category` |
|---------------------|------------------|
| `retrieval_result` not found | `retrieval_result_missing` |
| `retrieval_status` ≠ `completed` | `retrieval_result_not_completed` |
| `result_count` null or evidence count mismatch | `evidence_reference_missing` |
| Sort-time provenance join failure | `provenance_incomplete` |
| Invalid / unknown `ranking_profile` | `profile_not_allowed` |
| Default hash collision / in-flight duplicate | `duplicate_ranking` |
| Permutation validation P-01–P-07 failure | `permutation_mismatch` |
| Infrastructure / unexpected execution fault | `ranking_pipeline_unavailable` |
| Unclassified | `unknown_failure` |

**Prohibited categories:** `evidence_set_empty`, `invalid_request`, `retrieval_not_completed`, `permutation_violation`.

---

## 9. Worker model (OD-021)

### Locked doctrine

| Rule | Requirement |
|------|-------------|
| Workers | **Single-worker** ranking orchestration only |
| Concurrent ranking workers | **NOT AUTHORIZED** |
| Future concurrency | Explicit governance gate + `ranking_request_hash`-keyed advisory lock |

### Planned worker package (implementation phase — not authorized here)

```text
backend/app/workers/ranking_runtime/
```

| Mode | Lifecycle | Authorized in |
|------|-----------|---------------|
| Dry-run skeleton | `accepted` → `skipped` | Separate bounded task (mirror 007D) |
| Controlled execution | `accepted` → `completed` \| `failed` | TASK-008D implementation when authorized |

### Concurrent processing prevention (locked design)

1. **Process singleton:** one ranking worker process per environment (OD-021)
2. **V-08 in-flight guard:** reject new default execution when `accepted` result exists without terminal sibling for same request
3. **DB idempotency:** partial unique index on `ranking_request_hash` where `force_replay=false`
4. **Future (not authorized):** PostgreSQL advisory lock keyed by `ranking_request_hash` at execution start

Worker must call `execute_controlled_ranking` — not embed sort logic directly.

---

## 10. Test plan (design only)

**Planned test module:** `backend/tests/test_controlled_ranking_execution.py`

**No tests implemented by this authorization package.**

### Required test groups

| Group | Assertions |
|-------|------------|
| **Determinism** | Same retrieval + profile → identical `presentation_order_index` ordering across runs |
| **Permutation integrity** | Input/output multiset equality; P-01–P-07; `permutation_mismatch` on injected violation |
| **Profile ordering** | Golden-order fixtures per profile (`CANONICAL`, `EFFECTIVE_DATE_DESC`, `GROUP_BY_SOURCE`, `GROUP_BY_DOCUMENT`) |
| **Zero-evidence** | `completed`, `rank_count=0`, no ranked rows, no error |
| **Replay** | Default de-duplication; `force_replay` + nonce creates new row; DEC-011 hash behavior |
| **Persistence integration** | Only `create_*` ranking_persistence paths used; append-only history preserved |
| **Prohibited imports** | No `answer`, `ai`, `semantic`, `vector`, `retrieval_execution`, `CitationAssembler` in `ranking_execution` |
| **Single-worker enforcement** | In-flight `accepted` guard rejects duplicate default execution |

### Supplementary tests (recommended)

- `test_ranking_worker_skeleton.py` — dry-run `accepted` → `skipped` (when worker task authorized)
- Import guard parity with RK-10 / RE-01
- Canonical error vocabulary rejection of prohibited categories

---

## Explicit prohibitions (this task)

- No execution service code
- No ranking worker code
- No API endpoints
- No orchestration / background jobs
- No tests, models, migrations

---

## Authorization checklist (for future acceptance prompt)

- [ ] Architect accepts §1–§10 as implementation boundary
- [ ] Claude review of this package (recommended)
- [ ] Explicit prompt: **AUTHORIZED FOR LIMITED IMPLEMENTATION**
- [ ] Scope: `ranking_execution` service + tests (worker skeleton optional separate gate)

---

## Unresolved questions

| # | Question | Default recommendation |
|---|----------|----------------------|
| U-01 | Ship worker dry-run skeleton (`ranking_runtime`) in same task as controlled execution, or split like 007D → 007E? | **Split** — skeleton first (008D-1), controlled execution second (008D-2) |
| U-02 | Advisory lock (`pg_advisory_xact_lock`) in initial implementation or document-only until concurrency gate? | **Document-only** in v1; enforce via V-08 + single process |
| U-03 | Golden fixtures sourced from live DB seeds or static JSON envelopes? | **Static JSON** envelopes for determinism tests |

---

END OF TASK-008D IMPLEMENTATION AUTHORIZATION PACKAGE (implementation NOT AUTHORIZED)

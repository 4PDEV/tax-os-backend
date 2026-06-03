# Architecture Review — Citation Persistence Pre-Authorization (TASK-006Z)

**Review type:** Architecture review only — **not** implementation authorization  
**Date:** 2026-06-03  
**Scope:** Proposed `citation_assembly_requests` / `citation_assembly_results` persistence shape  
**Authority:** [`CITATION_ASSEMBLY_CONTRACT.md`](CITATION_ASSEMBLY_CONTRACT.md) (TASK-006Y), prior ingestion idempotency tasks (006P1, 006R, 006V, 006X1), [`LEGAL_OBJECT_PROMOTION_CONTRACT.md`](LEGAL_OBJECT_PROMOTION_CONTRACT.md) / migration `b5c3e9a04d47` (pattern reference)

**Verdict:** **APPROVED WITH REQUIRED REMEDIATION BEFORE TASK-006Z**

This review does **not** authorize citation execution, workers, retrieval, ranking, answers, legal advice, or tax/applicability inference.

---

## Executive summary

The proposed citation persistence architecture is **governance-consistent** with the platform doctrine chain and replay patterns established in 006P1, 006R, 006V, and 006X1.

**`legal_object_version_id` as default canonical citation assembly identity is correct.** It pins citations to a specific legal memory version, not a mutable `legal_object_id`.

Request/result-only persistence (no citation entity tables in 006Z) is the **correct phase boundary**, mirroring TASK-006V before controlled execution.

Three **required remediations** must be reflected in the TASK-006Z implementation spec before formal authorization:

1. Include **`legal_object_id`** on request and result (006Y-mandated provenance).
2. Resolve **naming collision** with TASK-004D `CitationAssemblyRequest` Pydantic model.
3. Complete **result shape** alignment with 006Y and promotion-result denormalization patterns.

---

## Platform state (review input)

| Item | Status |
|------|--------|
| TASK-006Y | Complete — citation governance established |
| Canonical Legal Memory | Closed (006U–006X + 006X1) |
| Citation persistence | Not started |
| TASK-006Z | Not authorized |
| Retrieval / answer runtime | Not authorized |

**Doctrine chain:** `parsed_structure` ≠ legal object · `legal_object` ≠ legal meaning · `legal_object` ≠ citation · `citation` ≠ answer

---

## Findings

### Z-01 — Request omits `legal_object_id`

| Field | Value |
|-------|-------|
| **Severity** | HIGH |
| **Governance contradiction?** | **Yes** — contradicts [`CITATION_ASSEMBLY_CONTRACT.md`](CITATION_ASSEMBLY_CONTRACT.md) §CitationAssemblyRequest and §Provenance |
| **Blocks TASK-006Z?** | **Yes** (authorization gate) |

**Title:** Missing denormalized `legal_object_id` on assembly request

**Exact risk:** Operators and auditors cannot validate request/result consistency against legal memory without joins; service-layer checks that `legal_object_version.legal_object_id` matches request intent are harder to enforce; provenance queries become version-only and may obscure object-level lineage breaks.

**Recommended remediation:** Add `legal_object_id` (FK → `legal_objects.legal_object_id`, NOT NULL) to `citation_assembly_requests` and denormalize on `citation_assembly_results`. Validate at write time that version belongs to object (same pattern as promotion `parsed_structure_id` + `source_version_id` pairing).

---

### Z-02 — Request omits denormalized `source_version_id`

| Field | Value |
|-------|-------|
| **Severity** | MEDIUM |
| **Governance contradiction?** | No — joinable via `legal_object_versions.source_version_id` |
| **Blocks TASK-006Z?** | No |

**Title:** Optional but recommended `source_version_id` on request

**Exact risk:** Full lineage audit (`source_version` → … → citation request) requires extra joins; inconsistent with TASK-006V promotion requests that record `source_version_id` at request time.

**Recommended remediation:** Add `source_version_id` (FK → `source_versions.id`, NOT NULL) on requests; validate consistency with the pinned `legal_object_version.source_version_id`.

---

### Z-03 — Name collision with TASK-004D `CitationAssemblyRequest`

| Field | Value |
|-------|-------|
| **Severity** | HIGH |
| **Governance contradiction?** | No — operational / maintainability risk |
| **Blocks TASK-006Z?** | **Yes** (authorization gate) |

**Title:** Persistence ORM/models must not reuse 004D assembler type names

**Exact risk:** `backend/app/services/citation/models.py` already defines `CitationAssemblyRequest` for deterministic assembler input. Import ambiguity, incorrect wiring, and test confusion between **governance persistence** and **004D implementation path**.

**Recommended remediation:** Use distinct persistence names, e.g. table `citation_assembly_requests`, ORM `CitationAssemblyGovernanceRequest` / module `app.services.citation_assembly_persistence` (or `ingestion_citation_assembly`). Document complementarity in TASK-006Z spec: 004D = assembler implementation; 006Z = ingestion lifecycle persistence.

---

### Z-04 — Result shape incomplete vs TASK-006Y and 006V pattern

| Field | Value |
|-------|-------|
| **Severity** | MEDIUM |
| **Governance contradiction?** | Partial — omits contract-mandated denormalized keys |
| **Blocks TASK-006Z?** | No (required remediation before implementation) |

**Title:** Result row missing version/object pins and contract timestamps

**Exact risk:** Results cannot be queried or audited by `legal_object_version_id` without joining requests; drift from promotion results which denormalize `parsed_structure_id` and `legal_object_id`.

**Recommended remediation:** Add to `citation_assembly_results`:

- `legal_object_id` (NOT NULL, FK)
- `legal_object_version_id` (NOT NULL, FK)
- `assembled_at` (nullable terminal timestamp — prefer over `completed_at` for 006Y alignment)
- `notes` (nullable)
- `citation_hash` (nullable on result **or** only on request — see Z-06; if request-only, omit from result)

Keep `citation_assembly_result_id` as UUID PK (`id`).

---

### Z-05 — `completed_at` vs `assembled_at` naming

| Field | Value |
|-------|-------|
| **Severity** | LOW |
| **Governance contradiction?** | No |
| **Blocks TASK-006Z?** | No |

**Title:** Prefer `assembled_at` for terminal success timestamp

**Exact risk:** Semantic drift from 006Y (`assembled` status / `assembled_at`) and parallel `promoted_at` in promotion results.

**Recommended remediation:** Use `assembled_at` on results; reserve `completed_at` only if a multi-phase lifecycle (queued/started) is introduced later (not required for 006Z).

---

### Z-06 — `citation_hash` placement (request vs result)

| Field | Value |
|-------|-------|
| **Severity** | LOW |
| **Governance contradiction?** | No — 006Y lists hash on result; 006V puts `promotion_hash` on request |
| **Blocks TASK-006Z?** | No |

**Title:** Hash on request aligns with promotion persistence; harmonize spec wording

**Exact risk:** Minor spec inconsistency between 006Y (result) and proposed shape (request). Implementation should follow **006V precedent**: `citation_hash` NOT NULL on **request**, default `sha256(legal_object_version_id)` for `force_reassembly=false`; distinct replay hash when `force_reassembly=true`.

**Recommended remediation:** Place `citation_hash` on request; index for lookup; do not include actor/reason/timestamps in default hash per 006Y.

---

### Z-07 — Dual hash namespace (ingestion vs TASK-004D)

| Field | Value |
|-------|-------|
| **Severity** | INFORMATIONAL |
| **Governance contradiction?** | No |
| **Blocks TASK-006Z?** | No |

**Title:** Ingestion `citation_hash` ≠ 004D rendered `citation_hash`

**Exact risk:** Future engineers conflate lifecycle idempotency hash (`legal_object_version_id`) with content hash (`source_version_id | legal_object_id | legal_object_version_id | location_reference` per 004D).

**Recommended remediation:** Document in TASK-006Z: **assembly_request_hash** (or keep `citation_hash` with module prefix in docs) vs **rendered_citation_hash** (004D output). No merge in 006Z.

---

### Z-08 — Identity doctrine confirmation

| Field | Value |
|-------|-------|
| **Severity** | INFORMATIONAL (positive) |
| **Governance contradiction?** | No |
| **Blocks TASK-006Z?** | No |

**Title:** `legal_object_version_id` is correct canonical default identity

**Assessment:** Correct. Aligns with version-pinned 004D assembler, 006X1 uniqueness on `(legal_object_id, text_hash)`, and replay doctrine across 006P1/006R/006V. No additional identity field required for 006Z default path. Optional future **assembly policy version** only if multiple default assembly policies per version are explicitly approved (006Y optional extension).

---

### Z-09 — Request/result-only scope for 006Z

| Field | Value |
|-------|-------|
| **Severity** | INFORMATIONAL (positive) |
| **Governance contradiction?** | No |
| **Blocks TASK-006Z?** | No |

**Title:** Citation entity tables correctly out of scope until execution phase

**Assessment:** No `citations` table exists today. 006Z should mirror 006V: append-only requests/results only. Materialized citation records (text, anchors, 004D `CitationResult` persistence) belong to a **post-006Z execution task**, not persistence-only 006Z.

---

### Z-10 — `citation_id` nullable until execution

| Field | Value |
|-------|-------|
| **Severity** | INFORMATIONAL (positive) |
| **Governance contradiction?** | No |
| **Blocks TASK-006Z?** | No |

**Title:** Nullable `citation_id` on results is correct for pre-execution persistence

**Assessment:** Required for dry-run skeleton parity (`skipped` with null `citation_id`). Do not FK to a non-existent citations table in 006Z.

---

### Z-11 — Status vocabulary

| Field | Value |
|-------|-------|
| **Severity** | INFORMATIONAL |
| **Governance contradiction?** | No |
| **Blocks TASK-006Z?** | No |

**Title:** Status set is consistent; document `skipped` semantics

**Assessment:** `pending`, `accepted`, `rejected`, `assembled`, `failed`, `skipped`, `duplicate_rejected` align with promotion and 006Y. **`skipped`** must mean orchestration completed without citation execution (006Y), not ignored request. **`assembled`** does not imply answers or applicability.

---

### Z-12 — Error categories

| Field | Value |
|-------|-------|
| **Severity** | INFORMATIONAL |
| **Governance contradiction?** | No |
| **Blocks TASK-006Z?** | No |

**Title:** Proposed error taxonomy is sufficient for persistence phase

**Assessment:** Categories cover eligibility, provenance, duplicates, and pipeline availability. Optional future addition: `version_not_eligible` (003E `version_status`) — not required to block 006Z if mapped to `version_missing` or `invalid_request` initially.

---

### Z-13 — Replay doctrine and partial unique index

| Field | Value |
|-------|-------|
| **Severity** | INFORMATIONAL (positive) |
| **Governance contradiction?** | No |
| **Blocks TASK-006Z?** | No |

**Title:** Partial unique on `legal_object_version_id WHERE force_reassembly = false` is correct

**Assessment:** Matches `uq_legal_object_promotion_requests_parsed_structure_default` and parsing/extraction trigger patterns. `force_reassembly` as sole bypass aligns with `force_repromotion` / `force_reparse`.

---

### Z-14 — OD-021 concurrency (persistence vs execution)

| Field | Value |
|-------|-------|
| **Severity** | MEDIUM |
| **Governance contradiction?** | No |
| **Blocks TASK-006Z?** | No |

**Title:** DB partial unique does not eliminate execution-time replay race

**Exact risk:** Under concurrent workers, two processes may pass application checks before either commits; creation-time idempotency is necessary but not sufficient for execution phase (same OD-021 as promotion).

**Recommended remediation:** Document in TASK-006Z implementation notes: single-worker acceptable on `main`; concurrent citation workers require advisory locks / row locks keyed by `legal_object_version_id` in a **future worker task** (not blocking 006Z tables).

---

### Z-15 — Provenance lineage

| Field | Value |
|-------|-------|
| **Severity** | INFORMATIONAL |
| **Governance contradiction?** | No (after Z-01/Z-02 remediation) |
| **Blocks TASK-006Z?** | No |

**Title:** Lineage complete via FK pins; no `parsed_structure_id` required on request

**Assessment:** Full chain is recoverable: `legal_object_version` → `legal_object` → `source_version` → upstream ingestion artifacts (`ps-{parsed_structure_id}` promotion identity). Request/result pins on `legal_object_id` + `legal_object_version_id` (+ recommended `source_version_id`) are sufficient. No lineage break if validation enforces version/object/source consistency.

---

### Z-16 — Temporal governance

| Field | Value |
|-------|-------|
| **Severity** | INFORMATIONAL |
| **Governance contradiction?** | No |
| **Blocks TASK-006Z?** | No |

**Title:** Persistence may store references only; must not infer temporal legal force

**Assessment:** 006Z tables should not add inferred effective/applicability columns. Temporal fields remain on `source_versions` / `legal_object_versions`. Citation assembly persistence records governance state only.

---

### Z-17 — Citation boundary maintenance

| Field | Value |
|-------|-------|
| **Severity** | INFORMATIONAL (positive) |
| **Governance contradiction?** | No |
| **Blocks TASK-006Z?** | No |

**Title:** Proposed shape maintains citation ≠ retrieval ≠ answer ≠ meaning

**Assessment:** Request/result tables without citation text, ranking scores, applicability flags, or answer payloads preserve boundaries. Risk increases only if later tasks store interpretive fields on these tables — out of scope for 006Z.

---

## Review question responses (summary)

| Question | Answer |
|----------|--------|
| Is `legal_object_version_id` correct canonical identity? | **Yes** |
| Aligns with 006P1/006R/006V/006X1? | **Yes** |
| Additional identity fields now? | **No** (default path) |
| Request/result sufficient for this phase? | **Yes** |
| Citation entities out of scope until execution? | **Yes** |
| Governance concerns with request/result-only? | **None** if Z-01–Z-04 remediated |
| `citation_id` nullable until execution? | **Yes** |
| Status vocabulary consistent? | **Yes** — document `skipped` |
| Error categories sufficient? | **Yes** |
| Replay / partial unique consistent? | **Yes** |
| Provenance complete? | **Yes** after Z-01/Z-02 |
| Temporal concerns? | **None** for persistence-only |
| Boundaries maintained? | **Yes** |
| OD-021 additional documentation? | **Yes** — Z-14 |

---

## Required remediation checklist (before TASK-006Z authorization)

| # | Remediation | Finding |
|---|-------------|---------|
| 1 | Add `legal_object_id` to request + result with FK + consistency validation | Z-01 |
| 2 | Distinct persistence module/model names from 004D `CitationAssemblyRequest` | Z-03 |
| 3 | Complete result shape: `legal_object_id`, `legal_object_version_id`, `assembled_at`, `notes`; CHECK constraints on status/error enums | Z-04, Z-05 |
| 4 | (Recommended) Add `source_version_id` on request with consistency validation | Z-02 |
| 5 | (Recommended) Document dual-hash namespaces in TASK-006Z spec | Z-07 |
| 6 | (Recommended) Document OD-021 execution mitigations for future worker task | Z-14 |

---

## Authorization boundary (unchanged)

This review **does not** authorize:

- TASK-006Z implementation (until separate explicit authorization after remediation)
- Citation workers or execution
- Retrieval, ranking, or answer runtime
- Legal advice or applicability inference

**Remediation package:** TASK-006ZA complete — [`CITATION_PERSISTENCE_REMEDIATION_006ZA.md`](CITATION_PERSISTENCE_REMEDIATION_006ZA.md). Findings Z-01–Z-05, Z-07, Z-14 addressed in planned shape.

**Next step:** Formal **remediation acceptance**, then separate explicit **AUTHORIZED FOR IMPLEMENTATION** for TASK-006Z. TASK-006Z remains **NOT AUTHORIZED** after 006ZA alone.

---

## References

- [CITATION_ASSEMBLY_CONTRACT.md](CITATION_ASSEMBLY_CONTRACT.md)
- [TASKS/TASK-006Y-CITATION-ASSEMBLY-CONTRACT.md](TASKS/TASK-006Y-CITATION-ASSEMBLY-CONTRACT.md)
- [LEGAL_OBJECT_PROMOTION_CONTRACT.md](LEGAL_OBJECT_PROMOTION_CONTRACT.md)
- [backend/app/services/citation/CITATION_ASSEMBLY_CONTRACT.md](backend/app/services/citation/CITATION_ASSEMBLY_CONTRACT.md) (TASK-004D)
- Migration `b5c3e9a04d47` (promotion persistence reference)
- [OPEN_DECISIONS.md](OPEN_DECISIONS.md) (OD-021)

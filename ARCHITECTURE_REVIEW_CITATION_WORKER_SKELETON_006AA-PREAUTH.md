# Architecture Review — Citation Worker Skeleton Pre-Authorization (TASK-006AA)

**Review type:** Pre-authorization architecture review only — **not** worker implementation  
**Date:** 2026-06-03  
**Scope:** Proposed **dry-run** citation assembly governance worker skeleton (orchestration over TASK-006Z persistence)  
**Authority:** [`CITATION_ASSEMBLY_CONTRACT.md`](CITATION_ASSEMBLY_CONTRACT.md), [`CITATION_PERSISTENCE_REMEDIATION_006ZA.md`](CITATION_PERSISTENCE_REMEDIATION_006ZA.md), TASK-006W / TASK-006O worker skeleton precedents

**Verdict:** **APPROVED FOR IMPLEMENTATION** (dry-run worker skeleton only — recommended task **TASK-006AB**)

This review does **not** authorize citation execution, TASK-004D rendering, retrieval, ranking, answers, or legal advice.

---

## Executive summary

A **dry-run citation assembly governance worker** mirroring TASK-006W is **architecturally sound** and consistent with the doctrine chain and TASK-006Z persistence.

The worker must orchestrate **governance lifecycle only**:

```text
citation_assembly_governance_request
  → accepted (result)
  → dry-run provider (no rendering)
  → skipped (result; citation_id null)
```

It must **not** produce `assembled` status, rendered citation text, `CitationResult` DTOs, or populated `citation_id` values in the skeleton phase.

---

## Mandatory boundary preservation (review confirms)

| Doctrine | Worker skeleton requirement | Preserved? |
|----------|----------------------------|------------|
| Governance result ≠ rendered citation | No `CitationAssembler`; `citation_id` always null; no citation content tables | **Yes** (if spec followed) |
| `citation` ≠ retrieval result | No retrieval imports or ranking | **Yes** |
| `citation` ≠ answer | No answer assembly | **Yes** |
| `legal_object` ≠ citation | Worker reads governance requests only; no legal-meaning inference | **Yes** |

---

## Proposed implementation envelope (TASK-006AB)

### Module / naming (required)

| Item | Value |
|------|--------|
| Package | `backend/app/workers/citation_assembly_governance/` |
| Worker class | `CitationAssemblyGovernanceWorker` |
| Provider protocol | `CitationAssemblyGovernanceProvider` |
| Dry-run provider | `DryRunCitationAssemblyGovernanceProvider` |
| Runner | `run_citation_assembly_governance_dry_run(db, *, dry_run=True)` — **must reject** if `dry_run=False` |

**Forbidden:** `CitationAssemblyWorker` in `backend/app/workers/citation/`; reuse of TASK-004D `CitationAssemblyRequest` / `CitationAssembler` types.

### Execution modes (006AB scope)

| Mode | Authorized in 006AB? |
|------|---------------------|
| `dry_run` | **Yes** — only mode |
| `controlled_assembly` / execution | **No** — future task + separate review gate |

### Orchestration flow (per eligible request)

1. Load `CitationAssemblyGovernanceRequest` rows (append-only scan).
2. `is_eligible()` — lineage + latest-result policy (mirror 006W).
3. `persist_citation_assembly_result(..., citation_status="accepted")`.
4. Invoke dry-run provider (synthetic success; **no** DB writes beyond results).
5. `persist_citation_assembly_result(..., citation_status="skipped", citation_id=None, assembled_at=None)`.

### Dry-run terminal status (critical)

| Field | Dry-run value |
|-------|----------------|
| `citation_status` | **`skipped`** — not `assembled` |
| `citation_id` | **null** |
| `assembled_at` | **null** |

**`skipped` semantics (006Y / 006W aligned):** orchestration completed without citation execution. **Not** “request ignored” (ineligible requests increment worker `requests_skipped` and do not append this terminal row).

### Eligibility policy (recommended)

Align with `LegalObjectPromotionWorker`:

- Validate actor type, `citation_reason`, lineage (`legal_object_id`, `legal_object_version_id`, `source_version_id`).
- Skip when latest result ∈ `{duplicate_rejected, rejected}`.
- Skip when latest terminal ∈ `{assembled, failed, skipped}` unless `force_reassembly=True`.
- Skip default requests when version already has terminal `assembled` / successful governance path (unless `force_reassembly`).

Use existing `app.services.citation_assembly_governance.persistence` — do not duplicate validation logic inconsistently.

### Provider contract (dry-run)

```python
class CitationAssemblyGovernanceProvider(Protocol):
    def run_assembly(
        self,
        db: Session,
        request: CitationAssemblyGovernanceRequest,
        legal_object_version: LegalObjectVersion,
    ) -> CitationAssemblyGovernanceProviderResult:
        ...
```

`DryRunCitationAssemblyGovernanceProvider` returns `success=True`, no `citation_id`, explicit notes that no rendering occurred.

### Explicit prohibitions (006AB)

- No `CitationAssembler` / `app.services.citation.assembler`
- No `CitationResult` persistence
- No retrieval (`app.services.retrieval`)
- No answer generation
- No AI/LLM
- No applicability / relevance / legal-meaning inference
- No second persistence table beyond 006Z request/result

---

## Findings

### AA-01 — Dry-run must not emit `assembled` status

| Field | Value |
|-------|-------|
| **Severity** | **HIGH** |
| **Governance contradiction?** | **Yes** if `assembled` without execution |
| **Blocks worker skeleton?** | **Yes** (spec violation) |

**Title:** Terminal status must be `skipped`, not `assembled`, in dry-run mode

**Exact risk:** Operators and downstream consumers interpret `assembled` as citation existence; violates 006Y dry-run doctrine and confuses governance lifecycle with rendering.

**Remediation:** Hard-code dry-run terminal `citation_status="skipped"`; reserve `assembled` for future controlled execution task only.

---

### AA-02 — TASK-004D assembler must remain unreachable

| Field | Value |
|-------|-------|
| **Severity** | **HIGH** |
| **Governance contradiction?** | **Yes** if assembler invoked |
| **Blocks worker skeleton?** | **Yes** |

**Title:** Worker package must not import or call TASK-004D citation rendering

**Exact risk:** Accidental rendering conflates governance `request_hash` with 004D content `citation_hash`; creates citation text without governed execution gate.

**Remediation:** Static boundary tests (forbidden imports); dry-run provider returns synthetic outcome only.

---

### AA-03 — Namespace separation from `app.services.citation`

| Field | Value |
|-------|-------|
| **Severity** | **HIGH** |
| **Governance contradiction?** | No — maintainability / boundary risk |
| **Blocks worker skeleton?** | **Yes** (authorization gate) |

**Title:** Worker lives under `citation_assembly_governance`, not `citation`

**Remediation:** Use `backend/app/workers/citation_assembly_governance/` per 006Z ORM naming.

---

### AA-04 — `skipped` vs worker `requests_skipped` counter

| Field | Value |
|-------|-------|
| **Severity** | MEDIUM |
| **Governance contradiction?** | No |
| **Blocks worker skeleton?** | No |

**Title:** Document dual meaning of “skipped”

**Remediation:** Copy 006W module docstring pattern into worker header and TASK-006AB record.

---

### AA-05 — `force_reassembly` eligibility

| Field | Value |
|-------|-------|
| **Severity** | MEDIUM |
| **Governance contradiction?** | No |
| **Blocks worker skeleton?** | No |

**Title:** Worker must honor `force_reassembly` replay doctrine

**Remediation:** Re-run eligibility when `force_reassembly=True` despite prior terminal `skipped`/`failed`; never bypass via `citation_reason` or actor alone.

---

### AA-06 — OD-021 execution-time race (informational for skeleton)

| Field | Value |
|-------|-------|
| **Severity** | INFORMATIONAL |
| **Governance contradiction?** | No |
| **Blocks worker skeleton?** | No |

**Title:** Single-worker assumption remains acceptable for 006AB

**Remediation:** Document in worker module: concurrent citation workers require advisory locks (future execution task); 006Z DB partial unique covers request creation only.

---

### AA-07 — Two append-only results per processed request

| Field | Value |
|-------|-------|
| **Severity** | INFORMATIONAL |
| **Governance contradiction?** | No |
| **Blocks worker skeleton?** | No |

**Title:** Mirror 006W `accepted` → terminal result pattern

**Assessment:** Preserves auditable lifecycle without mutating request rows.

---

### AA-08 — Governance persistence complete (positive)

| Field | Value |
|-------|-------|
| **Severity** | INFORMATIONAL (positive) |
| **Governance contradiction?** | No |
| **Blocks worker skeleton?** | No |

**Title:** TASK-006Z provides sufficient persistence substrate

**Assessment:** Request/result tables, `request_hash`, partial unique index, and service APIs are sufficient for skeleton orchestration.

---

## Review questions — answers

| Question | Answer |
|----------|--------|
| May dry-run worker skeleton be authorized? | **Yes** — as TASK-006AB only |
| Governance result ≠ rendered citation preserved? | **Yes** — if AA-01/AA-02 enforced |
| `citation` ≠ retrieval / answer preserved? | **Yes** — with AA-02/AA-03 |
| Jump to execution allowed? | **No** — separate future gate (e.g. TASK-006AC) |

---

## Required remediation checklist (before TASK-006AB implementation)

| # | Remediation | Finding |
|---|-------------|---------|
| 1 | Dry-run terminal `skipped`; never `assembled` in 006AB | AA-01 |
| 2 | No TASK-004D assembler imports or calls | AA-02 |
| 3 | Package `workers/citation_assembly_governance/` | AA-03 |
| 4 | Document `skipped` semantics in worker | AA-04 |
| 5 | `force_reassembly` eligibility policy | AA-05 |
| 6 | OD-021 note in worker module | AA-06 |

---

## Authorization boundary

| Item | Status after this review |
|------|--------------------------|
| TASK-006AA (this review) | **Complete** when recorded |
| TASK-006AB dry-run worker skeleton | **APPROVED FOR IMPLEMENTATION** — subject to remediation checklist + explicit governance acceptance |
| Citation execution / rendering | **NOT AUTHORIZED** |
| Retrieval / answers | **NOT AUTHORIZED** |

**Next step:** Record TASK-006AA acceptance → implement TASK-006AB per envelope above.

---

## References

- [CITATION_ASSEMBLY_CONTRACT.md](CITATION_ASSEMBLY_CONTRACT.md)
- [CITATION_PERSISTENCE_REMEDIATION_006ZA.md](CITATION_PERSISTENCE_REMEDIATION_006ZA.md)
- [TASKS/TASK-006W-LEGAL-OBJECT-PROMOTION-WORKER-SKELETON.md](TASKS/TASK-006W-LEGAL-OBJECT-PROMOTION-WORKER-SKELETON.md)
- [backend/app/workers/legal_object_promotion/worker.py](backend/app/workers/legal_object_promotion/worker.py)

# Temporal & Versioning Architecture

**Task:** TASK-005A-SPEC  
**Status:** Authoritative architecture specification (documentation only)  
**Version:** 1.0.0

This document defines how the Source-Referenced Business & Tax Research Platform handles time, versions, and legal state. It is the governing reference for all temporal behavior in retrieval, citation, and (future) answer assembly.

---

## 1. Core principle

The platform must never answer:

> What is the law?

The platform must answer:

> What was the law for this jurisdiction, for this tax type, on this date, based on available authorities?

**Time is a first-class architectural object.** Jurisdiction, tax type, and **as-of date** are mandatory context for any future answer or authority selection — not optional metadata.

---

## 2. Temporal philosophy

| Temporal state | Meaning | Platform obligation |
|----------------|---------|---------------------|
| **Past** | Historical legal state at a date before today | Reproducible retrieval and citation for any supported as-of date |
| **Present** | Current legal state (as-of today or operational “now”) | Explicit as-of date; never implicit “today” without recording it |
| **Future** | Published but not yet effective law | Representable and distinguishable from current law |
| **Unknown** | Timing cannot be established reliably | Flag ambiguity; never silently guess |

---

## 3. Temporal axes

Every authority should support multiple dates where available. These axes are **descriptive metadata** — not legal interpretation.

| Axis | Definition | Example |
|------|------------|---------|
| **Publication date** | When the authority became publicly available | 15 June 2025 |
| **Effective from** | When the authority becomes legally effective | 1 July 2025 |
| **Effective to** | When the authority ceases to be effective (nullable = open-ended) | 31 December 2026 |
| **Retrieval date** | When the platform acquired the source | `source_versions.retrieved_at` |
| **Processing date** | When the platform processed the source | Job completion / ingestion timestamps |

**Retroactive legislation:** Publication date and effective from **may differ**. Example: published June 2025, effective January 2025 — both must be representable without collapsing into a single date.

---

## 4. Versioning philosophy

**Nothing is overwritten. Ever.**

The platform preserves Version 1 → Version 2 → Version 3 through time. Historical legal states must remain **reproducible** for audit, citation, and dispute resolution.

| Layer | Versioning mechanism (current / planned) |
|-------|------------------------------------------|
| Source registry | `source_versions` append-only; `supersedes_version_id` chain |
| Legal objects | `legal_object_versions` immutable rows; `current_version_id` pointer only |
| Citations | Pinned `source_version_id` + `legal_object_version_id` (TASK-004D) |

Immutability rules from TASK-003E apply: versions are not destructively updated.

---

## 5. Source version governance

Every source version must support:

| Field | Purpose |
|-------|---------|
| `source_version_id` | Stable identity |
| `publication_date` | Public availability |
| `effective_from` | Legal start (nullable where unknown) |
| `effective_to` | Legal end (nullable = ongoing) |
| `supersedes_version_id` | Amendment / replacement chain |
| `version_status` | Lifecycle state |

### Recommended `version_status` values

| Status | Meaning |
|--------|---------|
| `draft` | Not yet authoritative for external answers |
| `active` | Currently effective or generally applicable |
| `superseded` | Replaced by a newer version; retained for history |
| `repealed` | No longer in force |
| `archived` | Retained for audit only; excluded from default retrieval |
| `future_effective` | Published; effective_from in the future |

**Governance:** Default retrieval and resolution must respect status filters (aligned with TASK-004A / 004B).

---

## 6. Legal object temporal model

Every legal object version must carry:

| Field | Requirement |
|-------|-------------|
| `effective_from` | Start of applicability for this version (nullable only when explicitly unknown) |
| `effective_to` | End of applicability (nullable = open-ended) |
| `source_version_id` | Link to authoritative source version |

A legal object **without temporal context is incomplete** for answer or citation purposes.

**Date rule (implemented — TASK-004B):**

```text
effective_from <= effective_on
AND (effective_to IS NULL OR effective_to >= effective_on)
```

---

## 7. Temporal query model (answer context)

Future answer engine inputs must include:

| Parameter | Required | Example |
|-----------|----------|---------|
| Jurisdiction | Yes | Rwanda (`RW`) |
| Tax type | Yes | VAT |
| Question | Yes | Input VAT recovery |
| **As-of date** | Yes | 15 March 2024 |

The as-of date is **fundamental retrieval context**, not a display preference.

### Query classes (test scenarios for later implementation)

| Class | Example question |
|-------|------------------|
| **Historical** | What was the VAT treatment on 15 March 2023? |
| **Current** | What is the treatment today? (must still record explicit as-of date) |
| **Future** | What will apply from 1 January 2027? |
| **Transitional** | What changed between 2024 and 2025? |

---

## 8. Amendment chain model

Amendments must preserve history:

```text
Original Provision → Amendment 1 → Amendment 2 → Amendment 3
```

### Recommended relationships

| Relationship | Direction | Purpose |
|--------------|-----------|---------|
| `supersedes_legal_object_id` | This object supersedes prior | Forward chain |
| `superseded_by_legal_object_id` | This object was superseded by | Reverse chain |

Source-level chains use `source_versions.supersedes_version_id`. Legal-object chains use lineage tables (TASK-003E) when persisted.

**Governance:** Supersession records lineage; it does not delete prior versions.

---

## 9. Future law support

The platform must represent authorities that are **published but not yet effective**.

Example:

- Finance Act enacted (publication_date: 2026-06-15)
- Effective: 1 January 2027 (effective_from: 2027-01-01)

### Distinctions required

| Label | Condition (conceptual) |
|-------|----------------------|
| **Current law** | effective_from ≤ as_of_date AND (effective_to IS NULL OR effective_to ≥ as_of_date) |
| **Future law** | effective_from > as_of_date (may be published) |

Future law must be **queryable separately** from current law — never merged silently into “the law.”

---

## 10. Answer-date resolution contract (future)

**Specification only — not implemented in TASK-005A.**

### Planned service boundary

```text
resolve_authorities_as_of(
    jurisdiction: str,
    tax_type: str,
    as_of_date: date,
) -> list[AuthorityResolutionResult]
```

### Purpose

Return the set of source versions and legal object versions **valid for the requested date**, with explicit status for each candidate:

- applicable
- not_applicable
- future_effective
- ambiguous_overlap
- missing_effective_date
- integrity_failed

### Relationship to existing modules

| Module | Role today |
|--------|------------|
| TASK-004A Retrieval | Deterministic fetch with optional `effective_on` filter |
| TASK-004B Effective-Date Resolver | Per–legal-object version resolution on `effective_on` |
| TASK-004C Citation Candidate | Prepares citation-ready DTOs with date status mapping |
| TASK-004D Citation Assembly | Assembles pinned, version-identified citations |
| **TASK-005A (this spec)** | Cross-authority temporal governance |
| **Future `resolve_authorities_as_of`** | Jurisdiction-wide authority set for an as-of date |

---

## 11. Temporal conflict handling

The architecture **preserves ambiguity**. It must **never silently guess**.

| Scenario | Required behavior |
|----------|-------------------|
| Overlapping effective periods | Flag `ambiguous_overlap`; do not pick a winner |
| Missing effective dates | Flag `missing_effective_date`; do not assume applicability |
| Conflicting publications | Surface both; require explicit resolution path |
| Retroactive amendments | Represent publication ≠ effective; resolve by as-of date rule |
| Repealed but historically relevant | Retain version; status `repealed` / `superseded`; historical queries use as-of date |

Aligned with TASK-004B `ResolutionStatus` and TASK-004C conservative candidate mapping.

---

## 12. Authority-type temporal extensions

Specification for future schema or metadata — **do not implement in TASK-005A**.

### Court decisions

| Field | Status |
|-------|--------|
| `decision_date` | Specify |
| `publication_date` | Specify |
| `overruled_date` | Deferred |
| `distinguished_date` | Deferred |

### Guidance

| Field | Status |
|-------|--------|
| `issued_date` | Specify |
| `withdrawn_date` | Specify (nullable) |

### Treaties

| Field | Status |
|-------|--------|
| `signed_date` | Specify |
| `ratified_date` | Specify |
| `effective_date` | Specify |

### Accounting standards

| Field | Status |
|-------|--------|
| `issued_date` | Specify |
| `mandatory_effective_date` | Specify |
| `early_adoption_allowed` | Specify (boolean or date range) |

---

## 13. Version selection principle

**Critical governance rule:**

The platform must **never** assume the **latest** version is correct.

| Prohibited | Required |
|------------|----------|
| Implicit “current” / `current_version_id` for citations or answers | Explicit `legal_object_version_id` pin (TASK-004D) |
| “Latest” `source_version` without as-of date | Date-aware selection via `effective_on` + status filters |
| Silent promotion of future law to current | Explicit `future_effective` handling |

Version selection is always **date-aware** and **explicitly pinned** at citation and (future) answer boundaries.

---

## 14. Platform stack alignment

```text
003A–003E  Persistence & integrity (immutable versions)
004A       Retrieval (effective_on filter, status filters)
004B       Effective-date resolver (applicability per legal object)
004C       Citation candidates (conservative date status mapping)
004D       Citation assembly (version-pinned output + lineage check)
005A-SPEC  Temporal & versioning architecture (this document)
```

---

## 15. Governance principles

1. **Time is not optional** — every authoritative output names an as-of date.
2. **Versions are immutable** — history is never overwritten.
3. **Ambiguity is preserved** — overlap and missing dates fail loud or flag explicit status.
4. **Future law is distinct** — published ≠ currently effective.
5. **Latest is not default** — date-aware, explicit version pins only.
6. **Publication ≠ effective** — retroactive legislation must be representable.
7. **Reproducibility** — same inputs (jurisdiction, tax type, as-of date, version pins) → same outputs.

---

## 16. Out of scope (TASK-005A)

This specification does **not** implement:

- answer engine
- legal reasoning or interpretation
- authority ranking or weighting
- temporal AI or inference of effective dates
- new database migrations (unless a future task authorizes)
- changes to existing resolver/citation code

---

## 17. Final principle

The platform's long-term trust depends on answering:

- the **right law**
- for the **right date**
- from the **right authority**
- using the **right version**

Everything else in the platform depends on this capability.

---

## Related documents

| Document | Role |
|----------|------|
| [TASKS/TASK-005A-TEMPORAL-VERSIONING-ARCHITECTURE-SPEC.md](TASKS/TASK-005A-TEMPORAL-VERSIONING-ARCHITECTURE-SPEC.md) | Approved task specification |
| [backend/app/services/effective_date/EFFECTIVE_DATE_RESOLVER_CONTRACT.md](backend/app/services/effective_date/EFFECTIVE_DATE_RESOLVER_CONTRACT.md) | Implemented per-object date resolution |
| [backend/app/services/citation/CITATION_ASSEMBLY_CONTRACT.md](backend/app/services/citation/CITATION_ASSEMBLY_CONTRACT.md) | Version-pinned citations |
| [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md) | Deferred hardening items |

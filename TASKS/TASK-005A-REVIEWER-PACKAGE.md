# TASK-005A-SPEC — Reviewer Package

**Purpose:** Single index of all files required to review TASK-005A (Temporal & Versioning Architecture Specification).

**Branch:** `feature/task-005a-temporal-versioning-architecture-spec`  
**Review type:** Documentation only — no code changes in TASK-005A-SPEC.

---

## 1. Core governance (architecture repository)

| # | File | Repository | Path |
|---|------|------------|------|
| 1 | Master Architecture v1 | `tax-os-architecture` | [`MASTER_ARCHITECTURE/PROJECT_SCOPE_AND_OPERATING_PRINCIPLES_v1.md`](../../tax-os-architecture/MASTER_ARCHITECTURE/PROJECT_SCOPE_AND_OPERATING_PRINCIPLES_v1.md) |
| 2 | **Addendum V5 — Temporal & Versioning** | `tax-os-architecture` | [`ADDENDUMS/ADDENDUM_V5_TEMPORAL_AND_VERSIONING_GOVERNANCE.md`](../../tax-os-architecture/ADDENDUMS/ADDENDUM_V5_TEMPORAL_AND_VERSIONING_GOVERNANCE.md) |

### Earlier addendums (context)

| Topic | File |
|-------|------|
| Trust, effective-date awareness, no fake confidence | [`ADDENDUM_v1_TRUST_AND_COMPLETENESS.md`](../../tax-os-architecture/ADDENDUMS/ADDENDUM_v1_TRUST_AND_COMPLETENESS.md) |
| Topic taxonomy (temporal complexity preserved) | [`ADDENDUM_v2_TOPIC_TAXONOMY_AND_QUERY_INTELLIGENCE.md`](../../tax-os-architecture/ADDENDUMS/ADDENDUM_v2_TOPIC_TAXONOMY_AND_QUERY_INTELLIGENCE.md) |
| AI orchestration governance | [`ADDENDUM_v3_AI_ORCHESTRATION_AND_AGENT_GOVERNANCE.md`](../../tax-os-architecture/ADDENDUMS/ADDENDUM_v3_AI_ORCHESTRATION_AND_AGENT_GOVERNANCE.md) |

---

## 2. Temporal specification (this repository) — **critical**

| # | File | Path |
|---|------|------|
| 3 | Authoritative temporal architecture | [`TEMPORAL_VERSIONING_ARCHITECTURE.md`](../TEMPORAL_VERSIONING_ARCHITECTURE.md) |

---

## 3. Task specification (this repository)

| # | File | Path |
|---|------|------|
| 4 | Approved TASK-005A spec | [`TASKS/TASK-005A-TEMPORAL-VERSIONING-ARCHITECTURE-SPEC.md`](TASK-005A-TEMPORAL-VERSIONING-ARCHITECTURE-SPEC.md) |

---

## 4. Related prior architecture — **alignment required**

Temporal architecture must align with immutability, citations, and source traceability.

### TASK-003E — Legal object persistence integrity & immutability

| Artifact | Path |
|----------|------|
| **Task spec** | [`TASKS/TASK-003E-LEGAL-OBJECT-PERSISTENCE-INTEGRITY.md`](TASK-003E-LEGAL-OBJECT-PERSISTENCE-INTEGRITY.md) |
| Integrity contract (implemented) | [`backend/app/services/legal_object_persistence/LEGAL_OBJECT_PERSISTENCE_INTEGRITY_CONTRACT.md`](../backend/app/services/legal_object_persistence/LEGAL_OBJECT_PERSISTENCE_INTEGRITY_CONTRACT.md) |
| Persistence repository contract | [`backend/app/services/legal_object_persistence/LEGAL_OBJECT_PERSISTENCE_REPOSITORY_CONTRACT.md`](../backend/app/services/legal_object_persistence/LEGAL_OBJECT_PERSISTENCE_REPOSITORY_CONTRACT.md) |
| Checkpoint | tag `checkpoint-task-003e` on `main` |

**Alignment checks:** immutable versions; no destructive updates; integrity hash; supersession guards; audit trail.

### TASK-004D — Citation assembly (+ AMENDMENT-A)

| Artifact | Path |
|----------|------|
| Task spec | [`TASKS/TASK-004D-CITATION-ASSEMBLY-CONTRACT.md`](TASK-004D-CITATION-ASSEMBLY-CONTRACT.md) |
| Amendment A spec | [`TASKS/TASK-004D-AMENDMENT-A-CITATION-IDENTITY-HARDENING.md`](TASK-004D-AMENDMENT-A-CITATION-IDENTITY-HARDENING.md) |
| Assembly contract | [`backend/app/services/citation/CITATION_ASSEMBLY_CONTRACT.md`](../backend/app/services/citation/CITATION_ASSEMBLY_CONTRACT.md) |
| Checkpoint | tag `checkpoint-task-004d` on `main` |

**Alignment checks:** explicit `legal_object_version_id` on citations; version-pinned hash; `SourceDocumentMismatchError`; never implicit latest.

### Source versioning & retrieval chain (004A–004C)

| Task | Contract / spec |
|------|-----------------|
| 004A Retrieval | [`backend/app/services/retrieval/LEGAL_OBJECT_RETRIEVAL_CONTRACT.md`](../backend/app/services/retrieval/LEGAL_OBJECT_RETRIEVAL_CONTRACT.md) |
| 004B Effective-date resolver | [`backend/app/services/effective_date/EFFECTIVE_DATE_RESOLVER_CONTRACT.md`](../backend/app/services/effective_date/EFFECTIVE_DATE_RESOLVER_CONTRACT.md) |
| 004C Citation candidate | [`backend/app/services/citation_candidate/CITATION_CANDIDATE_CONTRACT.md`](../backend/app/services/citation_candidate/CITATION_CANDIDATE_CONTRACT.md) |

### Source registry (foundational versioning)

| Artifact | Path |
|----------|------|
| `source_versions` model | [`backend/app/models/source_version.py`](../backend/app/models/source_version.py) |
| Immutability at API layer | [`backend/app/api/routes/source_versions.py`](../backend/app/api/routes/source_versions.py) (PUT/DELETE 405) |

---

## 5. Supporting governance (this repository)

| File | Purpose |
|------|---------|
| [`PROJECT_STATE.md`](../PROJECT_STATE.md) | Platform status including 005A section |
| [`TASK_REGISTRY.md`](../TASK_REGISTRY.md) | Task tracking |
| [`CHANGELOG.md`](../CHANGELOG.md) | `[task-005a-spec-complete]` entry |
| [`KNOWN_LIMITATIONS.md`](../KNOWN_LIMITATIONS.md) | Deferred temporal/citation items |
| [`OPEN_DECISIONS.md`](../OPEN_DECISIONS.md) | OD-011–OD-015 citation follow-ups |

---

## 6. Review focus

Confirm TASK-005A documentation:

- [ ] Does not contradict Master Architecture v1 or Addendum V5?
- [ ] Aligns with 003E immutability (nothing overwritten)?
- [ ] Aligns with 004B date rule and ambiguity preservation?
- [ ] Aligns with 004D version-pinned citations and lineage checks?
- [ ] States `resolve_authorities_as_of` as **future** only (not implemented)?
- [ ] No scope creep (no answer engine, AI inference, migrations, code)?

---

## 7. Absolute paths (VM layout)

If reviewing on the standard VM:

```text
/opt/tax-os/repos/tax-os-architecture/MASTER_ARCHITECTURE/PROJECT_SCOPE_AND_OPERATING_PRINCIPLES_v1.md
/opt/tax-os/repos/tax-os-architecture/ADDENDUMS/ADDENDUM_V5_TEMPORAL_AND_VERSIONING_GOVERNANCE.md
/opt/tax-os/repos/tax-os-backend/TEMPORAL_VERSIONING_ARCHITECTURE.md
/opt/tax-os/repos/tax-os-backend/TASKS/TASK-005A-TEMPORAL-VERSIONING-ARCHITECTURE-SPEC.md
```

---

END REVIEWER PACKAGE

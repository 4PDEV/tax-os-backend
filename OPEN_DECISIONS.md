# Open Decisions

Pending architectural or operational decisions. Resolve via `tax-os-architecture` and record outcome here.

| ID | Topic | Context | Status |
|----|-------|---------|--------|
| OD-001 | Test database provisioning | Auto-create `taxos_test` in fixture vs manual DBA step | Open |
| OD-002 | Docker compose location | Standardize compose file in repo vs `/opt/tax-os/infra` | Open |
| OD-003 | API URL prefix | Future `/api/v1` namespace vs flat routes | Open |
| OD-004 | Audit log writes | Which CRUD events write to `audit_log` first | Open |
| OD-005 | Storage backend | Local filesystem vs object storage for `storage_path` | Open |
| OD-006 | CI runner | GitHub Actions vs VM-only verification for integration tests | Open |
| OD-007 | Cross-reference persistence | When/how detected references are stored and linked to citation anchors or registry entities | Open |
| OD-008 | Cross-reference resolution | Whether target_candidate strings are resolved to source_versions automatically or remain unresolved surface labels until a dedicated task | Open |
| OD-009 | Structure parser vs segmentation | Whether `structure_parser` replaces, complements, or converges with `segmentation` generic segmenter for downstream legal-object work | Open |
| OD-010 | Legal object identity and dual extraction paths | **Governed (002H–003D merged).** Canonical input: `ConvergedLegalObjectCandidate`. Tables materialized (003C). Repository write path (003D merged). **CRUD APIs and ingestion wiring still blocked.** Lineage/duplicate table writes deferred — **TASK-003E approved.** Remaining after 003E: batch parent resolution, segment deprecation. | Governed — write path active; integrity enforcement next |

## Citation assembly (TASK-004D) — non-blocking / future review

| ID | Topic | Context | Status |
|----|-------|---------|--------|
| OD-011 | Citation formatter locale | `_format_date` uses locale-dependent month names (`strftime('%B')`); may affect cross-environment reproducibility of `citation_text` | Non-blocking / future review |
| OD-012 | Citation hash delimiter framing | Pipe-delimited hash payload; document canonical delimiter policy for future hash utilities | Non-blocking / future review |
| OD-013 | Shared canonical hash utility | Citation hash uses `sha256_text` from legal object extraction; consider shared governance module for cross-layer hashes | Non-blocking / future review |
| OD-014 | Formatter version on `citation_text` | `assembler_version` recorded; `citation_text` has no separate formatter version for audit replay | Non-blocking / future review |
| OD-015 | Authority classification fallback | `resolve_authority_type` maps unknown `source_type` via `authority_level` heuristics → `OTHER`; document explicit taxonomy governance | Non-blocking / future review |

## Temporal / integrity (post–TASK-005A review)

| ID | Topic | Context | Status |
|----|-------|---------|--------|
| OD-016 | **TASK-004E** — Citation temporal compliance | Remediate `CitationAssembler` silent `source_version` date fallback (Addendum V6 C1); spec in `TASKS/TASK-004E-CITATION-TEMPORAL-COMPLIANCE-REMEDIATION.md` | Planned |
| OD-017 | 003E enforcement reconciliation (IMP-4) | Align documented immutability rules with all read/update paths; post-merge review | Deferred / future review |
| OD-018 | Overlap ambiguity disclosure (IMP-6) | Enrich `AMBIGUOUS_OVERLAP` results with conflicting version identifiers for operators | Deferred / future review |

## Test gaps (QA)

| ID | Topic | Context | Status |
|----|-------|---------|--------|
| TEST-GAP-001 | Full-suite instability | Full-suite instability observed in legal-object integrity / retrieval tests during TASK-006A validation. Ingestion tests passed 12/12. Investigation deferred to bounded QA task (**TASK-006B**) before next migration-heavy task. | Open — blocks push confidence until TASK-006B |

## Decision Log (Closed)

| ID | Decision | Date |
|----|----------|------|
| — | *(none recorded yet)* | — |

When closing a decision, move row to Decision Log and reference approving task.

## StorageService Interface Scope

Current StorageService implementation includes:
- save_bytes
- read_bytes

Deferred decision:
- whether exists()
- whether delete()

These methods are intentionally deferred until:
- upload APIs
- ingestion agents
- lifecycle management
- retention workflows

Rationale:
avoid premature abstraction expansion before real ingestion workflows exist.
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
| OD-010 | Legal object identity and dual extraction paths | **Governed at contract level (TASK-002H).** Canonical model: `legal_object_extraction.models.LegalObjectCandidate`. Convergence boundary: `legal_object_convergence/`. **Persistence planning governed (TASK-002I):** only `ConvergedLegalObjectCandidate` may be planned for persistence; `legal_object_persistence_planning/` defines rules, risks, and phased migration — **no persistence implementation yet**. Implementation blocked until planning contract is architecturally approved. Remaining: batch parent resolution, segment deprecation timeline, cross-pipeline deduplication at persist time. | Governed — planning gate active |

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
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

## Decision Log (Closed)

| ID | Decision | Date |
|----|----------|------|
| — | *(none recorded yet)* | — |

When closing a decision, move row to Decision Log and reference approving task.

# Task Registry

Bounded task tracking for `tax-os-backend`. Authoritative specs remain in `tax-os-architecture`; this file tracks status.

| Task ID | Title | Status | Notes |
|---------|-------|--------|-------|
| TASK-001 | Source registry foundation | Complete | Models, initial schema |
| TASK-001C | Alembic infrastructure | Complete | `alembic.ini`, `env.py` |
| TASK-001E | Migration discipline | Complete | Upgrade/downgrade verified |
| TASK-001D/E | CRUD APIs (registry) | Complete | Tag `v0.1.1-crud-foundation` |
| TASK-001F | Baseline API tests | **Pending VM acceptance** | Implementation done; `pytest -q` on VM required |
| TASK-001G | Documentation + runbook | Complete | This documentation set |

## Status Legend

| Status | Meaning |
|--------|---------|
| Planned | Approved, not started |
| In progress | Active implementation |
| Pending VM acceptance | Code complete; VM verification required |
| Complete | Accepted and merged per governance |
| Deferred | Out of current phase |

## Adding Tasks

1. Approve task in architecture governance.
2. Add row to this table.
3. Implement on feature branch per [TASK_EXECUTION_STANDARD.md](TASK_EXECUTION_STANDARD.md).
4. Update [PROJECT_STATE.md](PROJECT_STATE.md) and [CHANGELOG.md](CHANGELOG.md) on completion.

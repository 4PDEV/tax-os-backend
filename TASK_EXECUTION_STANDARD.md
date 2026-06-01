# Task Execution Standard

Standard discipline for implementing bounded tasks in `tax-os-backend`.

## Task Lifecycle

| Phase | Activity |
|-------|----------|
| 1. Intake | Task approved with objective, scope, out-of-scope, acceptance criteria; **spec filed in `TASKS/TASK-<ID>-*.md`** (required for review) |
| 2. Branch | Create task-scoped feature branch |
| 3. Implement | Minimal change set aligned to spec |
| 4. Verify | Tests and operational checks per task |
| 5. Document | Update PROJECT_STATE, CHANGELOG, TASK_REGISTRY as applicable |
| 6. Review | Peer/Claude review against spec |
| 7. Accept | Explicit acceptance—VM verification when required |
| 8. Merge | Merge to main with checklist |

## Implementation Boundaries

Each task MUST define:

- **In scope** — what will change
- **Out of scope** — what must not change

Implementers stop at the boundary. New requirements require a new task.

Standing out-of-scope unless explicitly approved:

- architecture rewrites
- new public API surfaces beyond task spec
- auth, frontend, AI, embeddings, vector DB
- performance/load testing infrastructure
- CI/CD pipeline creation (unless task says so)

## Acceptance Criteria Handling

- Acceptance criteria are binary where possible (pass/fail).
- "Implemented" ≠ "Accepted" when VM or integration verification is specified.
- Skipped tests due to unreachable DB do not satisfy integration acceptance.
- Document acceptance status in `PROJECT_STATE.md`.

Example (TASK-001F):

- Implementation: accepted when code and skip guard exist.
- Final acceptance: pending until `pytest -q` passes on VM with PostgreSQL.

## Testing Requirements

| Change type | Minimum verification |
|-------------|---------------------|
| API behavior | Integration tests (`pytest -m integration`) on VM |
| Migrations | `upgrade head`, `downgrade -1`, `upgrade head` on test DB |
| Documentation-only | Peer review for accuracy |
| Immutability / governance | Explicit negative tests (e.g. 405 on PUT/DELETE) |

Run from repository root:

```bash
source .venv/bin/activate
export TEST_POSTGRES_HOST=localhost
export TEST_POSTGRES_PORT=5432
export TEST_POSTGRES_DB=taxos_test
export TEST_POSTGRES_USER=taxos
export TEST_POSTGRES_PASSWORD='<password>'
pytest -q
```

## Out-of-Scope Discipline

If a defect is found outside task scope:

- Record it in `KNOWN_LIMITATIONS.md` or open a new task.
- Do not fix drive-by unless task authorizes expansion.

## Rollback Expectations

Before merge, confirm rollback path:

- **Code:** revert git commit or merge revert PR.
- **Schema:** `alembic downgrade -1` if revision is reversible; otherwise forward-fix migration.
- **Data:** restore from backup per [BACKUP_AND_RECOVERY.md](BACKUP_AND_RECOVERY.md).

## Deliverables Checklist (Per Task)

- [ ] Spec file in `TASKS/` (required for reviewer — see [TASKS/README.md](TASKS/README.md))
- [ ] Code merged on feature branch
- [ ] Tests pass per acceptance rules
- [ ] Migrations reviewed (if applicable)
- [ ] Docs updated (if operational impact)
- [ ] PROJECT_STATE / TASK_REGISTRY / CHANGELOG updated
- [ ] Acceptance explicitly recorded

## Related Documents

- [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md)
- [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md)
- [MIGRATION_WORKFLOW.md](MIGRATION_WORKFLOW.md)

# Development Workflow

AI-assisted development governance for TAX-OS.

## Source of Truth

**GitHub** is the canonical source of truth for:

- application code
- migrations
- tests
- documentation

Chat sessions, IDE history, and local uncommitted work are not authoritative.

## Role Separation

| Role | Tool / owner | Responsibility |
|------|----------------|----------------|
| Architecture | ChatGPT (with `tax-os-architecture`) | Bounded task specs, principles, acceptance criteria |
| Implementation | Cursor | Code changes within task scope only |
| Review | Claude (or designated reviewer) | Scope, governance, risk, test adequacy |

Implementers must not expand architecture beyond approved tasks.

## Task Execution Flow

1. **Task approved** — documented in architecture repo or task brief (e.g. TASK-001F).
2. **Branch** — feature branch from `main` (e.g. `feature/task-001f-baseline-tests`).
3. **Implement** — minimal deterministic diff; no scope creep.
4. **Test** — VM verification for integration-dependent tasks.
5. **Review** — confirm boundaries, immutability rules, migration discipline.
6. **Merge** — only when acceptance criteria met.
7. **Update** — `PROJECT_STATE.md`, `CHANGELOG.md`, `TASK_REGISTRY.md`.

## Commit Discipline

- One task per commit series when possible.
- Commit message references task ID: `TASK-001F baseline API tests`.
- Do not commit secrets (`backend/.env`, credentials).
- Do not commit unrelated refactors.
- Do not amend pushed commits unless explicitly approved.

## Branch Discipline

- `main` remains deployable and documented.
- Feature branches are short-lived and task-scoped.
- Delete or archive branches after merge.

## Merge Discipline

Before merge:

- Acceptance criteria satisfied (including VM integration tests when required).
- Migrations reviewed and applied on dev.
- Documentation updated for operational impact.
- [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) items addressed for tagged releases.

Reject merges that:

- introduce auth, frontend, AI, or vector DB without task approval
- bypass Alembic for schema changes
- weaken `source_versions` immutability

## Implementation Constraints (Standing)

Do not add without explicit task approval:

- authentication / authorization
- frontend
- AI inference or embeddings
- vector databases
- ingestion agents
- unrelated refactors or async rewrites

## Related Documents

- [TASK_EXECUTION_STANDARD.md](TASK_EXECUTION_STANDARD.md)
- [TASK_REGISTRY.md](TASK_REGISTRY.md)
- [PROJECT_STATE.md](PROJECT_STATE.md)

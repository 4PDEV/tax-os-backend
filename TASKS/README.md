# Task specifications (`TASKS/`)

## Required for every task

Every approved implementation task **must** have its authoritative specification stored in this folder before review.

**Naming convention:**

```text
TASKS/TASK-<ID>-<SHORT-SLUG>.md
```

Examples:

- `TASK-004C-CITATION-CANDIDATE-CONTRACT.md`
- `TASK-004D-CITATION-ASSEMBLY-CONTRACT.md`

## Purpose

| Artifact | Role |
|----------|------|
| `TASKS/TASK-*.md` | Full approved spec — **reviewer source of truth** |
| `TASKS/TASK-*-REVIEWER-PACKAGE.md` | Index of all files required for review (when present) |
| `TASK_REGISTRY.md` | Status tracking only (not a substitute for the spec) |
| `*/CONTRACT.md` under `backend/app/services/` | Runtime contract documentation in code |

Reviewers compare implementation and PRs against the file in `TASKS/`, not against chat history or registry rows alone.

## When to create the file

Create or update the task spec file when the task is **approved for implementation** (same timing as opening the feature branch).

## Checklist (implementer)

- [ ] Spec file exists under `TASKS/` with correct task ID in the filename
- [ ] Spec includes objective, scope, out-of-scope, and acceptance criteria
- [ ] Spec committed on the feature branch before review is requested

## Checklist (reviewer)

- [ ] Open `TASKS/TASK-<ID>-*.md` for the task under review
- [ ] Verify PR scope matches the spec boundaries
- [ ] Do not approve merge if the `TASKS/` spec file is missing

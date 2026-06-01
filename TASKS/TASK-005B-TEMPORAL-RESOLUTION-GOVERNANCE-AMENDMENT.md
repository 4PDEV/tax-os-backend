# TASK-005B — TEMPORAL RESOLUTION GOVERNANCE AMENDMENT

## STATUS

APPROVED FOR IMPLEMENTATION

## OBJECTIVE

Apply Claude review findings to the temporal/versioning governance documents before merge of TASK-005A-SPEC.

This is a documentation/governance task only.

## BACKGROUND

Claude review identified valid temporal-governance issues:

| ID | Finding |
|----|---------|
| C1 | Citation Assembly Contract risks silently inheriting effective dates from `source_versions` |
| C2 | Temporal fields require correction/versioning discipline |
| C3 | Temporal status model must distinguish stored lifecycle status from derived temporal status |
| I1 | Transaction date and knowledge/observation date must be distinguished |
| I2 | Answer layer must never choose current law by default without explicit disclosure |
| I3 | `current_version_id` semantics must be tightly defined |
| I5 | current/future/expired temporal state should be derived dynamically |

## REQUIRED DELIVERABLES

1. `ADDENDUM_V6_TEMPORAL_RESOLUTION_AND_VERSION_PINNING.md` (architecture repository)
2. Amend `TEMPORAL_VERSIONING_ARCHITECTURE.md`
3. Amend `backend/app/services/citation/CITATION_ASSEMBLY_CONTRACT.md` (resolve C1)
4. Amend `TASKS/TASK-005A-TEMPORAL-VERSIONING-ARCHITECTURE-SPEC.md`
5. Update `PROJECT_STATE.md`, `CHANGELOG.md`

## OUT OF SCOPE

No code, models, migrations, tests, APIs, resolver implementation, or answer engine logic.

## ACCEPTANCE CRITERIA

- Addendum V6 exists with all required sections
- Architecture and citation contracts amended
- TASK-005A spec cross-references V6
- No implementation changes introduced

---

END OF TASK-005B

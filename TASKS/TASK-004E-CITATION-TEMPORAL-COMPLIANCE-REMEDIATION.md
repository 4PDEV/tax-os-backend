# TASK-004E — CITATION TEMPORAL COMPLIANCE REMEDIATION

## STATUS

**PLANNED** (registered pre-merge TASK-005A; not yet approved for implementation)

## OBJECTIVE

Remediate `CitationAssembler` temporal behavior to comply with Addendum V6 and the amended `CITATION_ASSEMBLY_CONTRACT.md`.

## BACKGROUND

Governance review (TASK-005B) identified that current assembly code uses:

```text
effective_from = version.effective_from or source_version.effective_from
effective_to = version.effective_to or source_version.effective_to
```

This **silently inherits** source-version dates when legal-object dates are absent — violating Addendum V6 (finding C1).

TASK-005B resolved C1 at **governance** level only. Code alignment is explicitly deferred to this task.

## REQUIRED CHANGES (WHEN APPROVED)

- Remove silent `source_version` date fallback for legal-object applicability display
- Populate provenance-marked fields when inherited dates are ever permitted
- Separate source-version temporal metadata from legal-object applicability in `CitationResult` (schema extension may be required)
- Update formatter to disclose unknown vs inherited vs native legal-object dates
- Tests proving no silent inheritance

## OUT OF SCOPE

- Answer engine
- Temporal resolver implementation
- Database migrations (unless required for provenance fields — separate approval)

## RELATIONSHIP

| Document | Role |
|----------|------|
| Addendum V6 | Governance rule |
| TASK-004D / AMENDMENT-A | Citation assembly baseline |
| TASK-005A / 005B | Temporal architecture |

## ACCEPTANCE CRITERIA (DRAFT)

- `CitationAssembler` compliant with Addendum V6
- No silent `or source_version.effective_*` fallback without provenance
- Contract tests updated
- Documented in `CITATION_ASSEMBLY_CONTRACT.md` implementation section

---

END OF TASK-004E (PLANNED)

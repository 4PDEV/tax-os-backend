# TASK-005A-SPEC — TEMPORAL & VERSIONING ARCHITECTURE SPECIFICATION

## STATUS

APPROVED FOR IMPLEMENTATION

## 1. OBJECTIVE

Define the authoritative temporal architecture for the Source-Referenced Business & Tax Research Platform.

This specification establishes how the platform handles:

- historical law
- future law
- effective dates
- publication dates
- amendment chains
- supersession
- answer date context
- version selection

This is one of the most critical architectural components of the entire platform.

Tax answers are often correct or incorrect solely because of timing.

## 2. CORE PRINCIPLE

The platform must never answer:

> What is the law?

The platform must answer:

> What was the law  
> for this jurisdiction  
> for this tax type  
> on this date  
> based on available authorities?

Time is a first-class architectural object.

## 3. TEMPORAL PHILOSOPHY

The platform must support:

**Past**

Historical legal state.

**Present**

Current legal state.

**Future**

Published but not yet effective law.

**Unknown**

Where timing cannot be established reliably.

## 4. TEMPORAL AXES

Every authority should support multiple dates where available.

**Publication Date**

When authority became public.

Example: 15 June 2025

**Effective From**

When authority becomes legally effective.

Example: 1 July 2025

**Effective To**

When authority ceases to be effective. Nullable.

**Retrieval Date**

When platform acquired source.

**Processing Date**

When platform processed source.

## 5. VERSIONING PHILOSOPHY

Nothing is overwritten. Ever.

The platform preserves:

Version 1 → Version 2 → Version 3 → …

through time.

Historical legal states must remain reproducible.

## 6. SOURCE VERSION GOVERNANCE

Every source version must support:

- source_version_id
- publication_date
- effective_from
- effective_to
- supersedes_version_id
- version_status

Recommended statuses:

- draft
- active
- superseded
- repealed
- archived
- future_effective

## 7. TEMPORAL QUERY MODEL

Future answer engine should support:

- Jurisdiction
- Tax Type
- Question
- **As Of Date**

Example:

Rwanda VAT — Input VAT recovery — As at: 15 March 2024

This becomes fundamental retrieval context.

## 8. LEGAL OBJECT TEMPORAL MODEL

Every legal object should support:

- effective_from
- effective_to
- source_version_id

A legal object without temporal context is incomplete.

## 9. AMENDMENT CHAIN MODEL

Support:

Original Provision → Amendment 1 → Amendment 2 → Amendment 3

without losing history.

Recommended relationships:

- supersedes_legal_object_id
- superseded_by_legal_object_id

## 10. FUTURE LAW SUPPORT

The platform must support published but not yet effective authorities.

Example: Finance Act enacted — Effective 1 January 2027

The platform should distinguish:

- Current Law
- Future Law

clearly.

## 11. ANSWER DATE RESOLUTION CONTRACT

Create future service contract:

```text
resolve_authorities_as_of(
    jurisdiction,
    tax_type,
    date
)
```

Purpose: Return authorities valid for requested date.

Implementation comes later. This task establishes specification only.

## 12. TEMPORAL CONFLICT HANDLING

Potential scenarios:

- Overlapping effective periods
- Missing effective dates
- Conflicting publications
- Retroactive amendments
- Repealed but still relevant historical provisions

The architecture must preserve ambiguity. Never silently guess.

## 13. RETROACTIVE LEGISLATION SUPPORT

Support: Publication Date ≠ Effective Date

Example:

- Published: June 2025
- Effective: January 2025

Must be representable.

## 14. COURT DECISION TEMPORALITY

Court decisions should support:

- decision_date
- publication_date

Later modules may add: overruled_date, distinguished_date

Do not implement now.

## 15. GUIDANCE TEMPORALITY

Guidance should support:

- issued_date
- withdrawn_date

where available.

## 16. TREATY TEMPORALITY

Treaties should support:

- signed_date
- ratified_date
- effective_date

where available.

## 17. ACCOUNTING STANDARD TEMPORALITY

Support:

- issued_date
- mandatory_effective_date
- early_adoption_allowed

where available.

## 18. VERSION SELECTION PRINCIPLE

The platform must never assume latest version is correct.

Version selection must be date-aware.

Critical governance rule.

## 19. TEST SCENARIOS TO SUPPORT LATER

Architecture must eventually support:

- **Historical Query** — What was the VAT treatment on 15 March 2023?
- **Current Query** — What is the treatment today?
- **Future Query** — What will apply from 1 January 2027?
- **Transitional Query** — What changed between 2024 and 2025?

## 20. OUT OF SCOPE

Do NOT implement:

- answer engine
- legal reasoning
- authority ranking
- temporal AI
- legal interpretation
- effective-date inference

This task is specification only.

## 21. ACCEPTANCE CRITERIA

TASK-005A-SPEC complete when:

- temporal philosophy documented
- versioning philosophy documented
- amendment chain model documented
- future-law support documented
- answer-date model documented
- conflict preservation rules documented
- governance principles documented

## 22. FINAL PRINCIPLE

The platform's long-term trust depends on answering:

- the right law
- for the right date
- from the right authority
- using the right version

Everything else in the platform depends on this capability.

---

END OF TASK-005A-SPEC

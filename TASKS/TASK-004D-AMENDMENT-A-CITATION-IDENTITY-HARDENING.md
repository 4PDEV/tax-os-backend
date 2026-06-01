# TASK-004D-AMENDMENT-A — Citation Identity Hardening

## STATUS

APPROVED FOR IMPLEMENTATION

## CONTEXT

TASK-004D implemented the Citation Assembly Contract and passed initial tests.

Claude architecture review identified merge-blocking governance issues.

Current branch:
`feature/task-004d-citation-assembly-contract`

Do NOT merge.
Do NOT tag.
Do NOT expand scope.

This amendment hardens citation identity before merge.

---

## OBJECTIVE

Ensure citation identity is fully version-pinned, deterministic, and audit-safe.

The current implementation requires legal_object_version_id as input, but citation identity/output does not preserve legal_object_version_id sufficiently.

This creates legal-memory risk.

Fix this before merge.

---

## REQUIRED CHANGES

### 1. Add legal_object_version_id to CitationResult

Update:

`backend/app/services/citation/models.py`

CitationResult must include:

`legal_object_version_id`

This field is mandatory.

---

### 2. Include legal_object_version_id in citation identity/hash

Update:

`backend/app/services/citation/hash.py`

Citation hash must include:

- source_version_id
- legal_object_id
- legal_object_version_id
- location_reference

Do NOT rely only on legal_object_id.

Required rule:

same legal_object_id + different legal_object_version_id
=
different citation_hash and citation_id

---

### 3. Update assembler output

Update:

`backend/app/services/citation/assembler.py`

Assembler must populate legal_object_version_id in CitationResult.

Do not infer latest/current version.

Use only explicit request/version-pinned input.

---

### 4. Add source_document consistency validation

Assembler must verify:

`source_version.source_document_id == legal_object.source_document_id`

or equivalent available fields in the current implementation.

If mismatch occurs, fail explicitly.

Create or reuse a clear exception.

Do NOT silently assemble citation across inconsistent source/document lineage.

---

### 5. Update tests

Update/add tests in:

- `backend/tests/test_citation_assembler.py`
- `backend/tests/test_citation_formatter.py` if affected

Required new tests:

A. CitationResult includes legal_object_version_id.

B. Same legal_object_id with different legal_object_version_id produces different citation_hash/citation_id.

C. Source document mismatch between legal_object and source_version fails.

D. Existing tests still pass.

---

### 6. Update contract documentation

Update:

`backend/app/services/citation/CITATION_ASSEMBLY_CONTRACT.md`

Must state:

- citation identity includes legal_object_version_id
- no citation identity may rely only on logical legal_object_id
- source_version/document consistency is required
- citations are version-pinned outputs, not only version-pinned inputs

---

### 7. Add governance note

Update:

- TASK_REGISTRY.md
- PROJECT_STATE.md
- CHANGELOG.md

Record:

TASK-004D-AMENDMENT-A — Citation Identity Hardening

Status:
implemented / pending review

---

## OUT OF SCOPE

Do NOT add:

- persistence
- database migrations
- APIs
- answer generation
- citation ranking
- authority weighting
- legal interpretation
- retrieval
- AI
- frontend changes
- broad refactors

Do NOT redesign the citation module.

This is a focused hardening amendment only.

---

## TEST REQUIREMENTS

Run:

```bash
pytest backend/tests/test_citation_formatter.py backend/tests/test_citation_assembler.py -v
```

Expected:
all tests pass

---

## ACCEPTANCE CRITERIA

Amendment complete only when:

- CitationResult contains legal_object_version_id
- citation_hash includes legal_object_version_id
- different legal object versions produce different citation identities
- source document mismatch fails explicitly
- contract docs updated
- governance docs updated
- tests pass
- no scope creep introduced

---

## COMMIT DISCIPLINE

Commit amendment separately:

```bash
git add .
git commit -m "TASK-004D-AMENDMENT-A citation identity hardening"
git push
```

Do NOT merge.

After push, return summary for renewed architecture review.

END TASK-004D-AMENDMENT-A

# TASK-007C1 Acceptance Review — Retrieval Persistence Remediation

**Review type:** Remediation acceptance — authorizes **TASK-007C** retrieval persistence implementation scope only  
**Date:** 2026-06-02  
**Closure date:** 2026-06-02  
**Authority:** [`RETRIEVAL_PERSISTENCE_REMEDIATION_007C1.md`](RETRIEVAL_PERSISTENCE_REMEDIATION_007C1.md), [`ARCHITECTURE_REVIEW_RETRIEVAL_PERSISTENCE_007C-PREAUTH.md`](ARCHITECTURE_REVIEW_RETRIEVAL_PERSISTENCE_007C-PREAUTH.md)

**Verdict:** **CLOSED** — **TASK-007C AUTHORIZED WITH CONDITIONS**

---

## Findings closed

| ID | Finding | Status |
|----|---------|--------|
| RP-01 | `request_hash` JSON canonicalization undefined | **CLOSED** |
| RP-02 | Evidence-reference provenance pins lack FK constraints | **CLOSED** |
| RP-03 | Citation-reference consistency unspecified | **CLOSED** |
| RP-04 | DB CHECK constraints not specified | **CLOSED** |
| RP-05 | `deterministic_order_index` uniqueness + derivation | **CLOSED** |
| RP-06 | `evidence_metadata` unconstrained leakage vector | **CLOSED** |
| RP-07 | Zero-result semantics undocumented | **CLOSED** |
| RP-08 | Prohibited-field doctrine not mechanically testable | **CLOSED** |

---

## Platform state after acceptance

| Layer / capability | Status |
|--------------------|--------|
| Extraction (006M–006P1) | **COMPLETE** |
| Parsing (006Q–006T1A) | **COMPLETE** |
| Legal object layer (006U–006X1) | **COMPLETE** |
| Citation layer (006Y–006AD) | **COMPLETE** |
| Retrieval runtime contract (007B) | **COMPLETE** |
| Retrieval persistence design (007C1) | **COMPLETE** |
| **TASK-007C** retrieval persistence | **AUTHORIZED FOR IMPLEMENTATION** |
| TASK-007D retrieval execution | **NOT AUTHORIZED** |
| Ranking | **NOT AUTHORIZED** |
| Answer runtime | **NOT AUTHORIZED** |
| AI retrieval | **NOT AUTHORIZED** |
| Concurrent retrieval workers (OD-021) | **NOT AUTHORIZED** |

---

## Authorization envelope (TASK-007C — persistence only)

**Approved for implementation only:**

| Item | Scope |
|------|--------|
| Tables | `retrieval_requests`, `retrieval_results`, `retrieval_evidence_references` |
| Persistence mode | Append-only — no updates, no hard deletes |
| Request identity | `request_hash = SHA-256(canonical_json(normalized_retrieval_envelope))` |
| Hash includes | `retrieval_mode`, `as_of_date`, `legal_object_version_id`, `jurisdiction_code`, `tax_type_code`, `scope_envelope`, `include_canonical_text`, `include_rendered_citation_text` |
| Hash excludes | `query_text`, actor fields, timestamps, `notes`, database IDs |
| Force replay | Distinct hash material via replay nonce |
| DB guard | Partial unique on `request_hash` WHERE `force_replay = false` |
| Order constraint | `UNIQUE(retrieval_result_id, deterministic_order_index)` |
| FK pins | `legal_objects`, `legal_object_versions`, `source_versions`, `citations` (nullable) |
| Citation consistency | `citation_id` ⇔ `citation_hash`; version/object/source pins must match evidence |
| Citation mismatch | `retrieval_status = failed`, `error_category = provenance_incomplete` — never silent drop/substitution |
| Metadata whitelist | `structural_path`, `source_label`, `citation_label`, `object_label`, `object_type`, `location_reference`, `deterministic_sort_key`, `provenance_notes` |
| Prohibited metadata | `answer_text`, `legal_conclusion`, `applicability_flag`, `ranking_score`, `relevance_score`, `confidence_score`, `semantic_score`, `ai_output`, `llm_output`, `recommendation`, `advice`, `interpretation` |
| Zero-result semantics | `completed` + `result_count = 0` = successful empty retrieval |
| Tests (RP-08) | Prohibited columns absent; metadata keys rejected; answer/ranking/AI fields cannot persist |
| ORM names | `RetrievalRequest`, `RetrievalResult`, `RetrievalEvidenceReference` |
| OD-021 | Single-worker only — concurrent workers behind future lock-based gate |

**Conditions on TASK-007C authorization:**

1. Implementation must conform to [`RETRIEVAL_PERSISTENCE_REMEDIATION_007C1.md`](RETRIEVAL_PERSISTENCE_REMEDIATION_007C1.md) and [`RETRIEVAL_RUNTIME_CONTRACT.md`](RETRIEVAL_RUNTIME_CONTRACT.md).
2. Persistence stores **governed evidence references only** — not answers, rankings, or interpretations.
3. **007D** (worker/execution) requires separate authorization after 007C completion.
4. Ranking, answers, AI retrieval, and concurrent workers remain **not authorized**.

**Explicitly not authorized in TASK-007C:**

- Retrieval workers or runtime execution (007D)
- HTTP/API routes for retrieval
- Semantic / vector / AI search
- Ranking or answer generation
- Modification of TASK-004A behavior
- Concurrent retrieval workers (OD-021)

---

## Doctrine chain (unchanged)

```text
parsed_structure ≠ legal object
legal_object ≠ legal meaning
legal_object ≠ citation
citation ≠ retrieval result
retrieval result ≠ answer
```

Retrieval persistence stores governed evidence references. It must not become answer storage, ranking storage, or a provenance bypass.

---

## Governed pipeline (retrieval layer)

```text
TASK-007A   Review
  → TASK-007A1 Remediation
  → TASK-007A1 Acceptance
  → TASK-007B  Retrieval Runtime Contract
  → TASK-007C  Pre-Auth Review
  → TASK-007C1 Remediation
  → TASK-007C1 Acceptance (this document)
  → TASK-007C  Retrieval Persistence        ← authorized now
  → TASK-007D  Worker / Execution           ← not authorized
  → Retrieval Layer Review                  ← future gate
```

Mirrors citation governance maturity before 006Z implementation.

---

## Next gate

**TASK-007C** — deliver append-only retrieval persistence per this authorization envelope.

After 007C acceptance: **TASK-007D** retrieval worker/execution pre-authorization (not yet open).

---

END OF TASK-007C1 ACCEPTANCE REVIEW

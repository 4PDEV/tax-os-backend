# Answer Assembly Contract

## Purpose

Define governed boundaries for **answer assembly** — constructing a source-referenced answer package from completed ranking output and retrieval provenance.

This contract is **governance only** (TASK-009A-PREAUTH). It authorizes the answer assembly **design envelope** for downstream bounded implementation. It does **not** authorize answer runtime services, workers, persistence, migrations, APIs, response runtime, or AI-assisted answer generation.

## Core principle

**Answer assembly composes a governed, source-referenced answer package from ranked evidence — it does not retrieve, rank, invent evidence, or conclude legal force.**

```text
ranking_request (completed terminal result)
  → ranked_evidence_references (via accepted ranking_result)
  → retrieval_evidence_references (provenance read — DEC-010)
  → citation / legal_object_version / source_version (read-only joins)
  → answer package (governed output)
```

Answer assembly is **not**:

- evidence retrieval or re-selection
- ranking or reordering of evidence
- evidence invention, substitution, or silent omission
- provenance duplication or mutation
- citation creation or re-assembly of canonical citations
- legal advice, applicability determination, or legal conclusion
- semantic / vector search or AI ranking
- unconstrained LLM answer generation from model memory

## Mandatory doctrines

| Doctrine | Rule |
|----------|------|
| `retrieval result` ≠ ranking | Answer assembly does not perform retrieval |
| `ranking` ≠ answer | Answer assembly consumes ranking output only — no re-ranking |
| `answer` ≠ legal conclusion | Answer text is source-referenced exposition; no legal-force inference |
| **Provenance lives once** (DEC-010) | Pins authoritative in `retrieval_evidence_references`; answer reads via joins |
| **Source-referenced only** (DEC-002) | Every answer entry must trace to persisted provenance |
| **Ambiguity surfaced** (DEC-005) | Conflicts and uncertainty must be explicit — no silent certainty |
| **Deterministic-first** | Same ranking output + same assembly inputs → same answer package structure |
| **Single-worker carry-forward** (OD-021) | Concurrent answer workers not authorized until explicit governance gate |

Upstream contracts (binding, closed):

- [`RETRIEVAL_RUNTIME_CONTRACT.md`](RETRIEVAL_RUNTIME_CONTRACT.md) (007B)
- [`RANKING_RUNTIME_CONTRACT.md`](RANKING_RUNTIME_CONTRACT.md) (008B-v2)
- [`RANKING_EXECUTION_CONTRACT.md`](RANKING_EXECUTION_CONTRACT.md) (008D)
- [`CITATION_ASSEMBLY_CONTRACT.md`](CITATION_ASSEMBLY_CONTRACT.md) (006Y / 004D layers)
- [`TASKS/RANKING-LAYER-REVIEW.md`](TASKS/RANKING-LAYER-REVIEW.md) (008A+ accepted)
- [`DECISION_LOG.md`](DECISION_LOG.md) — DEC-001 through DEC-013

---

## 1. Answer layer boundary

### Inputs (required)

Answer assembly **must** consume only:

| Input | Source | Requirement |
|-------|--------|-------------|
| Completed ranking lifecycle | `ranking_requests` + terminal `ranking_results` | Terminal `ranking_status = completed` |
| Ranked evidence set | `ranked_evidence_references` | Loaded from **accepted** `ranking_result` for the same `ranking_request_id` (RL-O-01) |
| Retrieval provenance | `retrieval_evidence_references` | Read-only join via `retrieval_evidence_reference_id` |
| Upstream provenance | `legal_object_version`, `citation`, `source_version` | Read-only joins only — no re-resolution |
| Assembly parameters | Future `answer_request` envelope | `contract_version`, display flags — governance-defined only |

**Ranking result resolution (binding — closes RL-O-01):**

```text
1. Validate ranking_request exists
2. Load terminal ranking_result for request where ranking_status = completed
3. Load accepted ranking_result for same ranking_request_id (ranking_status = accepted)
4. Load ranked_evidence_references WHERE ranking_result_id = accepted.id
   ORDER BY presentation_order_index ASC
5. Verify len(ranked_rows) == terminal.rank_count
```

Answer assembly **must not** accept a bare terminal `ranking_result_id` without verifying the accepted-row ranked attachment and terminal `completed` status.

### Outputs

| Output | Description |
|--------|-------------|
| **Answer package** | Governed `AnswerPackage` structure (§5) — source-referenced, ordered, auditable |

### Boundary statements (required)

Answer assembly:

- **consumes** ranking output (completed lifecycle + ranked pointers)
- **does not perform** ranking (no `ranking_profile`, no permutation, no `presentation_order_index` mutation)
- **does not perform** retrieval (no `retrieval_execution`, no evidence selection, no `result_count` changes)

**Prohibited input bypass:**

- Direct consumption of `retrieval_evidence_references` without ranked path
- Consumption of non-completed ranking lifecycle (`accepted`-only, `failed`, in-flight)
- Reordering by any key other than `presentation_order_index` from ranked rows

---

## 2. Evidence usage rules

### Ranked-evidence-only doctrine

| Rule | Requirement |
|------|-------------|
| **E-01** | Answer evidence entries **must** correspond 1:1 to `ranked_evidence_references` for the accepted ranking result |
| **E-02** | Entry order **must** follow `presentation_order_index` ascending — no reordering |
| **E-03** | No retrieval bypass — provenance loaded only through ranked row pointers |
| **E-04** | No evidence invention — no synthetic `retrieval_evidence_reference_id` or fabricated pins |
| **E-05** | No silent omission — every ranked row produces an answer evidence entry unless assembly fails explicitly |
| **E-06** | No silent addition — no evidence entries outside the ranked multiset |
| **E-07** | Multiplicity preserved — duplicate ranked rows produce duplicate answer entries (no deduplication) |
| **E-08** | Zero-evidence ranking (`rank_count = 0`) → valid empty evidence list; not an error |

### Omission rules (explicit only)

Evidence may be **excluded from answer text** only when:

| Condition | Behaviour |
|-----------|-----------|
| Assembly validation failure | `answer_status = failed` with canonical `error_category` |
| Governed display flag (future) | Explicit per-entry `included_in_answer = false` with `exclusion_reason` — **not authorized in 009A-PREAUTH** |

**Prohibited omission patterns:**

- Relevance filtering
- Top-N truncation
- Authority weighting suppression
- Semantic similarity filtering
- "Best evidence only" selection

---

## 3. Provenance rules (DEC-010)

### Read model

Answer assembly obtains provenance **exclusively** via join chain:

```text
ranked_evidence_reference
  → retrieval_evidence_reference (FK)
    → legal_object_id, legal_object_version_id, source_version_id
    → citation_id, citation_hash (when present)
    → object_identifier, location_reference, evidence_metadata
  → legal_object_version (read)
  → citation (read, when citation_id present)
  → source_version (read)
```

### Required behaviours

| Rule | Requirement |
|------|-------------|
| **P-01** | Provenance stored once in `retrieval_evidence_references` — answer layer reads only |
| **P-02** | Answer layer **must not** persist copied provenance fields on answer-owned rows (when persistence is authorized) |
| **P-03** | Answer package **may** include provenance **references** (IDs, hashes, pointers) — not authoritative duplicates |
| **P-04** | Answer layer **must not** mutate retrieval, ranking, citation, or legal-object rows |
| **P-05** | Version pins (`legal_object_version_id`) **must not** be re-resolved or upgraded to "latest" |

### Prohibited on answer-owned persistence (future)

When answer persistence is authorized, prohibited columns mirror ranking prohibitions plus:

- `legal_conclusion`, `applicability_flag`, `authority_weight`, `relevance_score`
- `ranking_score`, `semantic_score`, `ai_score`, `confidence_score`
- Copied `citation_hash`, `effective_from`, or full citation body as authoritative store (references only)

---

## 4. Citation assembly rules

### Model (governance — no implementation)

Answer-layer citation handling is **reference construction and optional read-only rendering** — not citation creation.

| Concept | Rule |
|---------|------|
| **Citation reference** | Pointer bundle: `citation_id`, `citation_hash`, `legal_object_version_id`, `retrieval_evidence_reference_id` |
| **Rendered citation text** | Optional read-only display derived from persisted `citations` entity or governed formatter — labeled as stored text, not new authority |
| **Citation ordering** | Follows `presentation_order_index` of parent ranked row — no citation-level re-sort |
| **Missing citation** | When `citation_id` is null on retrieval evidence: entry permitted with `citation_reference_status = absent` — assembly may continue if contract allows; must not fabricate citation |

### Relationship to existing citation governance

| Layer | Role in answer assembly |
|-------|-------------------------|
| `CITATION_ASSEMBLY_CONTRACT.md` (006Y) | Canonical citation **creation** governance — answer layer **must not** invoke creation paths |
| `backend/app/services/citation/` (004D) | Deterministic **read-only** text assembly from version pins — permitted only when explicitly authorized in implementation task; not authorized by 009A-PREAUTH |
| Retrieval evidence | Supplies `citation_id` / `citation_hash` references — answer reads these pins |

### Prohibited

- New citation creation during answer assembly
- `CitationAssembler` invocation that mutates canonical citation state
- Re-assembly that changes citation identity or hash
- Citation ordering independent of ranked evidence order
- Citation text presented as legal conclusion or applicability determination

---

## 5. Answer structure

### Contract generation

`contract_version`: **`009A-v1`** (current pre-auth generation)

### AnswerPackage (governance schema)

```text
AnswerPackage
├── answer_package_id          UUID (surrogate — assigned at assembly time)
├── contract_version           string — "009A-v1"
├── ranking_request_id         UUID — FK reference
├── retrieval_result_id        UUID — denormalized reference for audit
├── terminal_ranking_result_id UUID — completed ranking_result.id
├── accepted_ranking_result_id UUID — accepted ranking_result.id (ranked row parent)
├── ranking_profile            string — read from ranking_request (audit only)
├── rank_count                 int — must equal len(evidence_entries)
├── answer_status              enum — see lifecycle
├── assembled_at               datetime (UTC)
├── evidence_entries           ordered list[AnswerEvidenceEntry]
├── uncertainty_flags          list[UncertaintyFlag] — may be empty
├── assembly_metadata          AnswerAssemblyMetadata — optional audit block
├── error_category             string | null — when answer_status = failed
└── error_message              string | null — when answer_status = failed
```

### AnswerEvidenceEntry

```text
AnswerEvidenceEntry
├── presentation_order_index   int — copied from ranked row (1..N)
├── ranked_evidence_reference_id UUID
├── retrieval_evidence_reference_id UUID
├── retrieval_result_id        UUID
├── legal_object_id            string — provenance reference (read)
├── legal_object_version_id    UUID — provenance reference (read)
├── source_version_id          UUID — provenance reference (read)
├── citation_reference         CitationReference | null
├── object_identifier          string | null — from retrieval evidence
├── location_reference         string | null — from retrieval evidence
├── citation_reference_status  enum — present | absent | incomplete
└── entry_metadata             dict | null — non-authoritative display hints only
```

### CitationReference

```text
CitationReference
├── citation_id                string | null
├── citation_hash              string | null
└── rendered_citation_text     string | null — optional; read-only; not authoritative
```

### UncertaintyFlag

```text
UncertaintyFlag
├── flag_type                  enum — conflict | ambiguity | incomplete_provenance | zero_evidence | other
├── severity                   enum — informational | warning | error
├── message                    string — human-readable; not legal advice
└── related_evidence_ids       list[UUID] — retrieval_evidence_reference_id values
```

### AnswerAssemblyMetadata

```text
AnswerAssemblyMetadata
├── requested_by_actor_type    string | null
├── assembly_mode              enum — deterministic (only mode in 009A-v1)
├── display_flags              dict | null — future governed flags
└── notes                      string | null
```

### Answer lifecycle statuses

| `answer_status` | Meaning |
|-----------------|---------|
| `completed` | Answer package assembled; `evidence_entries` populated per rules |
| `failed` | Terminal error; `error_category` required |
| `skipped` | Reserved — dry-run / no-op (future worker skeleton) |

**Prohibited fields on AnswerPackage:**

- `legal_conclusion`, `applicability_determination`, `tax_advice`, `recommendation_text` (as authoritative fields)
- `ranking_score`, `relevance_score`, `confidence_score`, `authority_weight`
- Copied full provenance blobs replacing join references as authoritative store

**Answer text (future extension):**

Narrative `answer_text` blocks, if authorized in a later contract generation, must:

- Reference `evidence_entries` by ID — no orphan claims
- Carry explicit uncertainty when DEC-005 applies
- Not constitute legal conclusion (DEC-001, DEC-013)

Narrative generation is **not authorized** by TASK-009A-PREAUTH.

---

## 6. Failure model

Answer assembly uses a **distinct canonical error vocabulary**. Ranking errors **must not** be reused as answer-layer terminal categories without explicit mapping at an orchestration boundary.

### Canonical answer error categories

| `error_category` | Meaning |
|----------------|---------|
| `ranking_result_not_completed` | Terminal ranking result missing or not `completed` |
| `accepted_ranking_result_missing` | No `accepted` ranking_result for request (RL-O-01 violation) |
| `ranked_evidence_missing` | No ranked rows when `rank_count > 0` |
| `evidence_count_mismatch` | `len(ranked_rows) != terminal.rank_count` |
| `provenance_chain_incomplete` | Required join target missing (e.g. `legal_object_version`) |
| `citation_reference_incomplete` | Citation required by assembly mode but pin absent |
| `retrieval_result_mismatch` | Ranked row `retrieval_result_id` ≠ ranking request scope |
| `assembly_validation_failed` | E-01–E-07 rule violation detected |
| `answer_pipeline_unavailable` | Persistence or dependency failure |
| `unknown_failure` | Unclassified terminal failure |

### Prohibited answer error categories

| Term | Reason |
|------|--------|
| `permutation_mismatch` | Ranking-layer — not answer assembly |
| `duplicate_ranking` | Ranking-layer idempotency |
| `profile_not_allowed` | Ranking-layer |
| `retrieval_result_not_completed` | Retrieval-layer prerequisite (orchestration may map to `ranking_result_not_completed`) |
| `evidence_set_empty` | Prohibited legacy term |

### Failure behaviour

- On failure: `answer_status = failed`; populate `error_category` + `error_message`
- **Must not** mutate retrieval, ranking, or citation authoritative rows
- **Must not** partially persist authoritative provenance duplicates
- Append-only answer lifecycle (when persistence authorized) — no in-place mutation of prior packages

---

## 7. Layer separation

### Retrieval layer (007A–007E) — **CLOSED**

| Responsibility | Boundary |
|----------------|----------|
| Evidence selection | Selects version-pinned evidence into `retrieval_evidence_references` |
| Provenance authority | Owns evidence pins and `deterministic_order_index` |
| Output | `retrieval_result` with `retrieval_status = completed` |

**Answer layer must not:** execute retrieval, change evidence membership, create retrieval rows.

### Ranking layer (008B–008D, U-01) — **CLOSED**

| Responsibility | Boundary |
|----------------|----------|
| Presentation order | Permutes evidence via `ranking_profile` |
| Pure pointers | `ranked_evidence_references` — order only (DEC-010) |
| Output | Completed ranking lifecycle + ranked multiset |

**Answer layer must not:** execute ranking, change `presentation_order_index`, apply profiles.

### Answer layer (009A+) — **PRE-AUTH ONLY**

| Responsibility | Boundary |
|----------------|----------|
| Package assembly | Build `AnswerPackage` from ranked + provenance reads |
| Citation references | Construct reference bundles; optional read-only rendering |
| Uncertainty surfacing | DEC-005 flags in package |
| Output | Governed answer package — not legal conclusion |

**Answer layer must not:** retrieval, ranking, citation creation, legal inference, unauthorized AI.

### Downstream (not authorized)

| Layer | Status |
|-------|--------|
| Response runtime | **NOT AUTHORIZED** |
| Public APIs | **NOT AUTHORIZED** |
| Answer persistence (009B+) | **NOT AUTHORIZED** |
| Answer worker (009C+) | **NOT AUTHORIZED** |

---

## 8. AI boundary

### Not authorized (009A-PREAUTH)

| Capability | Status |
|------------|--------|
| Semantic ranking | **NOT AUTHORIZED** |
| Vector / embedding ranking | **NOT AUTHORIZED** |
| Retrieval re-selection | **NOT AUTHORIZED** |
| LLM answer generation from model memory | **NOT AUTHORIZED** (DEC-001) |
| AI relevance filtering of evidence | **NOT AUTHORIZED** |
| AI citation creation or rewriting | **NOT AUTHORIZED** |
| AI legal conclusion or applicability inference | **NOT AUTHORIZED** |
| Unbounded prompt-driven assembly | **NOT AUTHORIZED** |

### Governance-defined AI (future only)

Any AI involvement in answer assembly requires:

1. Separate governance task and contract amendment
2. Explicit input/output boundaries (no provenance mutation)
3. Source-referenced output requirement preserved (DEC-002)
4. Human-review or audit envelope defined
5. No override of ranked evidence set (E-01–E-07)

**009A-v1 assembly mode:** `deterministic` only — join reads and structural package assembly.

---

## 9. Readiness criteria (implementation authorization)

Implementation of answer assembly (**TASK-009A implementation and beyond**) is **NOT AUTHORIZED** until all criteria below are satisfied:

### Governance gates

| # | Criterion | Status at 009A-PREAUTH |
|---|-----------|------------------------|
| G-01 | Ranking layer review accepted (008A+) | **MET** |
| G-02 | Answer assembly contract exists (this document) | **MET** |
| G-03 | DEC-013 locked | **MET** (this pre-auth) |
| G-04 | Claude / reviewer acceptance of 009A-PREAUTH | **PENDING** |
| G-05 | Implementation authorization package (009A-IMPL-AUTH or equivalent) | **NOT STARTED** |

### Design gates (pre-implementation)

| # | Criterion | Required before code |
|---|-----------|---------------------|
| D-01 | Ranking result resolution rule (accepted vs terminal) documented and test-planned | **MET** (§1) |
| D-02 | AnswerPackage schema frozen for contract generation | **MET** (§5) |
| D-03 | Answer error vocabulary distinct from ranking | **MET** (§6) |
| D-04 | Evidence usage rules E-01–E-08 test plan | **PENDING** (implementation auth) |
| D-05 | Import boundary guards defined (no retrieval_execution, ranking_execution writes) | **PENDING** (implementation auth) |
| D-06 | OD-021 carry-forward for answer worker documented | **PENDING** (implementation auth) |
| D-07 | Answer persistence scope decision (ephemeral vs append-only) | **OPEN** (see §10) |
| D-08 | Narrative `answer_text` authorization decision | **OPEN** — not in 009A-v1 |
| D-09 | CitationFormatter / CitationAssembler read-only usage decision | **OPEN** |
| D-10 | Response runtime handoff contract | **NOT STARTED** |

### Implementation prohibitions (unchanged until explicit authorization)

- No `answer_assembly` service package
- No answer workers, APIs, ORM models, migrations, or tests
- No AI/semantic/vector integration
- No concurrent answer workers (OD-021)

---

## 10. Explicit prohibitions

| Capability | Status |
|------------|--------|
| Answer runtime implementation | **NOT AUTHORIZED** |
| Answer persistence | **NOT AUTHORIZED** |
| Answer workers | **NOT AUTHORIZED** |
| HTTP / public APIs | **NOT AUTHORIZED** |
| Retrieval execution | **NOT AUTHORIZED** in answer layer |
| Ranking execution | **NOT AUTHORIZED** in answer layer |
| Citation creation | **NOT AUTHORIZED** in answer layer |
| AI / semantic / vector ranking | **NOT AUTHORIZED** |
| Legal conclusions | **NOT AUTHORIZED** |
| Concurrent answer workers | **NOT AUTHORIZED** (OD-021) |

---

## 11. Import boundaries (planned — enforcement at implementation)

Answer assembly code (when authorized) **must not** import:

- `app.services.retrieval_execution`
- `app.services.ranking_execution` (write paths)
- `app.services.ai`, `app.services.semantic`, `app.services.vector`
- Citation creation / mutation paths

Permitted read paths (when explicitly authorized in implementation task):

- `app.services.retrieval_persistence` (read APIs only)
- `app.services.ranking_persistence` (read APIs only)
- `app.services.citation` (read-only formatter/assembler — if D-09 closed)

---

## 12. Sequencing

```text
007A–007E  Retrieval (complete)
  → 008B–008D, U-01  Ranking (complete)
  → 008A+  Ranking layer review (accepted)
  → 009A-PREAUTH  Answer assembly contract (this document)
  → [Claude review]
  → 009A-IMPL-AUTH  Implementation authorization (not started)
  → 009A  Answer assembly implementation (NOT AUTHORIZED)
  → Answer layer review (future)
  → Response runtime (NOT AUTHORIZED)
```

---

END OF ANSWER ASSEMBLY CONTRACT (TASK-009A-PREAUTH — governance only)

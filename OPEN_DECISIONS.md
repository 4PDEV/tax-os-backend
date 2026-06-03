# Open Decisions

Pending architectural or operational decisions. Resolve via `tax-os-architecture` and record outcome here.

| ID | Topic | Context | Status |
|----|-------|---------|--------|
| OD-001 | Test database provisioning | Auto-create `taxos_test` in fixture vs manual DBA step | Open |
| OD-002 | Docker compose location | Standardize compose file in repo vs `/opt/tax-os/infra` | Open |
| OD-003 | API URL prefix | Future `/api/v1` namespace vs flat routes | Open |
| OD-004 | Audit log writes | Which CRUD events write to `audit_log` first | Open |
| OD-005 | Storage backend | Local filesystem vs object storage for `storage_path` | Open |
| OD-006 | CI runner | GitHub Actions vs VM-only verification for integration tests | Open |
| OD-007 | Cross-reference persistence | When/how detected references are stored and linked to citation anchors or registry entities | Open |
| OD-008 | Cross-reference resolution | Whether target_candidate strings are resolved to source_versions automatically or remain unresolved surface labels until a dedicated task | Open |
| OD-009 | Structure parser vs segmentation | Whether `structure_parser` replaces, complements, or converges with `segmentation` generic segmenter for downstream legal-object work | Open |
| OD-010 | Legal object identity and dual extraction paths | **Governed (002H–003D merged).** Canonical input: `ConvergedLegalObjectCandidate`. Tables materialized (003C). Repository write path (003D merged). **CRUD APIs and ingestion wiring still blocked.** Lineage/duplicate table writes deferred — **TASK-003E approved.** Remaining after 003E: batch parent resolution, segment deprecation. | Governed — write path active; integrity enforcement next |

## Citation assembly (TASK-004D) — non-blocking / future review

| ID | Topic | Context | Status |
|----|-------|---------|--------|
| OD-011 | Citation formatter locale | `_format_date` uses locale-dependent month names (`strftime('%B')`); may affect cross-environment reproducibility of `citation_text` | Non-blocking / future review |
| OD-012 | Citation hash delimiter framing | Pipe-delimited hash payload; document canonical delimiter policy for future hash utilities | Non-blocking / future review |
| OD-013 | Shared canonical hash utility | Citation hash uses `sha256_text` from legal object extraction; consider shared governance module for cross-layer hashes | Non-blocking / future review |
| OD-014 | Formatter version on `citation_text` | `assembler_version` recorded; `citation_text` has no separate formatter version for audit replay | Non-blocking / future review |
| OD-015 | Authority classification fallback | `resolve_authority_type` maps unknown `source_type` via `authority_level` heuristics → `OTHER`; document explicit taxonomy governance | Non-blocking / future review |

## Temporal / integrity (post–TASK-005A review)

| ID | Topic | Context | Status |
|----|-------|---------|--------|
| OD-016 | **TASK-004E** — Citation temporal compliance | Remediate `CitationAssembler` silent `source_version` date fallback (Addendum V6 C1); spec in `TASKS/TASK-004E-CITATION-TEMPORAL-COMPLIANCE-REMEDIATION.md` | Planned |
| OD-017 | 003E enforcement reconciliation (IMP-4) | Align documented immutability rules with all read/update paths; post-merge review | Deferred / future review |
| OD-018 | Overlap ambiguity disclosure (IMP-6) | Enrich `AMBIGUOUS_OVERLAP` results with conflicting version identifiers for operators | Deferred / future review |

## Extraction pipeline (post–TASK-006P review)

| ID | Topic | Context | Status |
|----|-------|---------|--------|
| OD-019 | Extraction replay / idempotency hardening | EXT-01 / F-05 remediated in TASK-006P1: canonical idempotency on `source_version_id`, partial unique DB index, source_version-level worker skip; `rerun_allowed` records policy only and does not bypass; `force_reprocess=True` is explicit bypass | **Resolved (TASK-006P1)** |
| OD-020 | Trigger `completed` vs text-ready semantics | `trigger_status=completed` on dry-run does not imply `extracted_text` exists; consumers must join `extracted_text` / check extractor identity | Documented — non-blocking |
| OD-021 | Multi-worker ingestion race (extraction + parsing + promotion + citation) | **OPEN / INFORMATIONAL** — single-worker operating constraint remains acceptable on `main`. Concurrent promotion or citation workers require execution-time replay race mitigation before enablement. Creation-time idempotency closed (006P1, 006R, 006V, L-02b). LOW now, MEDIUM under concurrency | Open — deferred |
| OD-022 | Parsed structure identity (P-01) | `UNIQUE(parsed_structures.parser_run_id)` in TASK-006T1A; verified at `checkpoint-task-006t1a-parsed-structure-identity` | **Closed (TASK-006T1A)** |

## Parsing pipeline — review closed (006Q–006T, 006T1A)

| ID | Topic | Context | Status |
|----|-------|---------|--------|
| P-01 | `parsed_structure` identity | One structure per `parser_run` at DB + service | **Closed (006T1A)** |
| P-02 | Parser persistence / hash verification | Eligibility/status-trust LOW; `sha256_structure()` deterministic | **Closed (006T1A verification)** |
| V-1 | Migration test visibility gap | Informational; non-blocking | Deferred / maintenance |
| V-2 | Hash sort-key hardening | Informational; optional future maintenance | Deferred / maintenance |

**Reviews:** [`CLAUDE_REVIEW_PARSING_PIPELINE_006Q-T.md`](CLAUDE_REVIEW_PARSING_PIPELINE_006Q-T.md) **CLOSED** · [`CLAUDE_VERIFICATION_PARSED_STRUCTURE_IDENTITY_006T1A.md`](CLAUDE_VERIFICATION_PARSED_STRUCTURE_IDENTITY_006T1A.md) **VERIFIED** (2026-06-02).

**Legal-object promotion gate:** **CLOSED** (Claude review 006U–006X, 2026-06-03 — **APPROVED FOR CONTINUE**). L-01, L-02, L-02b **CLOSED**.

**Citation layer:** **OPEN** — TASK-006Y **AUTHORIZED** (citation assembly contract, governance-only). No citation persistence (006Z), answer generation, or retrieval runtime until explicitly approved.

Doctrine: `parsed_structure` ≠ legal object; `legal_object` ≠ legal meaning; `legal_object` ≠ citation ≠ answer.

## Test gaps (QA)

| ID | Topic | Context | Status |
|----|-------|---------|--------|
| TEST-GAP-001 | Full-suite instability | Observed during TASK-006A validation. Root cause isolated in TASK-006B (service-level rollback scope + stale migration downgrade assumption + unstable resolver ordering). Fixed; full suite now passes 3 consecutive runs. | **Resolved (TASK-006B)** |

## Decision Log (Closed)

| ID | Decision | Date |
|----|----------|------|
| TEST-GAP-001 | Full-suite instability resolved in TASK-006B | 2026-06-02 |
| OD-019 | Extraction replay / idempotency (EXT-01 / F-05) | TASK-006P1 | 2026-06-02 |
| OD-022 | Parsed structure identity (P-01) | TASK-006T1A | 2026-06-02 |
| P-01 | Parsed structure one-per-parser_run | TASK-006T1A | 2026-06-02 |
| P-02 | Parser persistence/hash verification | 006T1A verification | 2026-06-02 |
| 006Q–006T | Parsing pipeline architecture review | Claude sign-off | 2026-06-02 |
| L-01 | LegalObjectType vocabulary structural-only | 006U–006X review | 2026-06-03 |
| L-02 | Canonical legal-memory write path append-only | 006U–006X review | 2026-06-03 |
| L-02b | `UNIQUE(legal_object_id, text_hash)` on `legal_object_versions` | TASK-006X1 | 2026-06-03 |
| 006U–006X | Legal object promotion pipeline review | **APPROVED FOR CONTINUE** | 2026-06-03 |

When closing a decision, move row to Decision Log and reference approving task.

## StorageService Interface Scope

Current StorageService implementation includes:
- save_bytes
- read_bytes

Deferred decision:
- whether exists()
- whether delete()

These methods are intentionally deferred until:
- upload APIs
- ingestion agents
- lifecycle management
- retention workflows

Rationale:
avoid premature abstraction expansion before real ingestion workflows exist.
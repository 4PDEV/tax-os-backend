# Task Registry

Bounded task tracking for `tax-os-backend`. Authoritative specs remain in `tax-os-architecture` and in **`TASKS/TASK-<ID>-*.md`** (required for reviewer); this file tracks implementation status only.

| Task ID | Title | Status | Notes |
|---------|-------|--------|-------|
| TASK-001 | Source Registry & Versioned Source Storage Foundation | Complete | Foundational deterministic source infrastructure |
| TASK-001A | Runtime Foundation | Complete | FastAPI, config, DB session |
| TASK-001B | Core DB Models | Complete | Registry schema models |
| TASK-001C | Alembic Migrations | Complete | Migration discipline |
| TASK-001D | CRUD + Internal Admin APIs | Complete | Tag `v0.1.1-crud-foundation` |
| TASK-001E | Alembic Migration Discipline | Complete | Upgrade/downgrade/rebuild verified |
| TASK-001F | Baseline API Tests | Complete | VM integration verification required for merge acceptance |
| TASK-001G | Documentation + Operational Runbook | Complete | Governance and ops docs |
| TASK-001H | Storage Abstraction + Checksum Utility | Complete | Local storage, path safety, unit tests |
| TASK-001I | Timezone-aware UTC timestamps | Complete | `utc_now()` across models |
| TASK-001J | Source Upload Internal API | Complete | `POST /source-versions/{id}/upload` |
| TASK-001K | Source Version File Attachment Workflow | Complete | Attachment state, API metadata, docs |
| TASK-001L | Source Ingestion Status + Workflow State Machine | Complete | `ingestion_status` field, governed transitions, internal API |
| TASK-001M | Source Processing Queue Table | Complete | `source_processing_jobs`, retry-aware job status transitions |
| TASK-001N | Processing Job Claim / Lock API | Complete | `claim-next`, `locked_at`/`locked_by`, SKIP LOCKED |
| TASK-001O | Processing Job Result / Completion API | Complete | `/complete`, `/fail`, result metadata, ingestion sync |
| TASK-001P | Worker Contract + No-op Harness | Complete | `SourceJobProcessor`, `run_next_job_once`, lifecycle tests |
| TASK-002A | Source Text Extraction Contract | Complete | Extraction contract/models/enums, SHA-256 hashing, `BaseExtractor`, TXT extractor, PDF/HTML skeletons |
| TASK-002B | Structural Source Segmentation Contract | Complete | Segmentation contract/models/enums, `BaseSegmenter`, deterministic `GenericSegmenter` (offsets + hierarchy), legislative skeleton |
| TASK-002C | Legal Object Extraction Contract | Complete | Legal object contract/models/enums, `BaseLegalObjectExtractor`, deterministic `GenericLegalObjectExtractor` (segment→object mapping), legislative skeleton |
| TASK-002D | Canonical Citation Anchor Contract | Complete | Citation anchor contract/models/enums, `BaseCitationAnchorGenerator`, deterministic `GenericCitationAnchorGenerator` (structure-based anchors + SHA-256 id + lineage), legislative skeleton |
| TASK-002E | Cross-Reference Detection Contract | Complete | `CrossReferenceResult`, `CrossReferenceDetector`, deterministic regex patterns, confidence model, no persistence |
| TASK-002F | Structural Section Parser Contract | Complete | `StructuralUnit`, `StructuralParser`, hierarchy resolution, heading extraction, offset preservation, no persistence |
| TASK-002G | Structural Legal Object Extraction Contract | Complete | `LegalObjectExtractor`, deterministic `legal_object_id`, canonical paths; merged — tag `task-002g-merged` |
| TASK-002H | Legal Object Candidate Convergence Contract | Complete | OD-010 governed at contract level; merged — tag `task-002h-merged` |
| TASK-002I | Legal Object Persistence Planning Contract | Complete | Persistence governance only; merged — tag `task-002i-merged` |
| TASK-003A | Canonical Legal Object Persistence Schema Contract | Complete | Schema planning only; merged — tag `task-003a-merged` |
| TASK-003B | Canonical Legal Object SQLAlchemy Models | Complete | ORM definitions; merged — tag `task-003b-merged` |
| TASK-003C | Canonical Legal Object Alembic Migration | Complete | Revision `f7c2d9e41a83`; merged — tag `task-003c-merged` |
| TASK-003D | Legal Object Persistence Repository Contract | Complete (merged) | Write path from `ConvergedLegalObjectCandidate`; merged — tag `task-003d-merged` |
| TASK-003E | Legal Object Persistence Integrity & Immutability Enforcement | Complete (merged) | Integrity baseline frozen — tag `checkpoint-task-003e`; merge `0213fb1` |
| TASK-004A | Legal Object Retrieval Contract | Complete (merged) | Deterministic retrieval — tag `checkpoint-task-004a`; merge `90357ff` |
| TASK-004B | Effective-Date Resolver Contract | Complete (merged) | Time-aware resolution — tag `checkpoint-task-004b`; merge `08efa3b` |
| TASK-004C | Citation Candidate Contract | Complete (merged) | Citation-ready DTO preparation — tag `checkpoint-task-004c`; merge `1349eb7` |
| TASK-004D | Citation Assembly Contract | Complete (merged) | Deterministic citation assembly — tag `checkpoint-task-004d`; merge `0588637` |
| TASK-004D-AMENDMENT-A | Citation Identity Hardening | Complete (merged) | Version-pinned citation identity + lineage enforcement — merged with 004D |
| TASK-005A-SPEC | Temporal & Versioning Architecture | Complete (merged) | Governance spec — tag `checkpoint-task-005a-spec`; merge `43c6ad0` |
| TASK-005B | Temporal Resolution Governance Amendment | Complete (merged) | Addendum V6 + doc amendments — merged with 005A-SPEC |
| TASK-004E | Citation Temporal Compliance Remediation | Planned | Align `CitationAssembler` with Addendum V6 — code task; defer unless blocking |
| TASK-006A | Source Ingestion Persistence Layer | Complete (main) | Append-only extraction/parser persistence — commit `acc32e4`; TEST-GAP-001 |
| TASK-006B | Test Isolation & Full-Suite Stability | Complete (merged) | TEST-GAP-001 resolved; 3 consecutive full-suite passes; test DB safety guard + fixture hardening |
| TASK-006C | Source Monitoring Agent Contract | Complete | Governance and contract boundaries only; no live monitoring/scraping/schedulers |
| TASK-006D | Source Monitoring Candidate Persistence | Complete | Monitoring persistence tables/services; append-only candidate transitions; no live monitoring |
| TASK-006E | Source Monitoring Worker Skeleton | Complete | Dry-run-only worker lifecycle; synthetic provider; non-dry-run rejected |
| TASK-006F | Controlled Source Fetch Contract | Complete | Fetch governance contract only; no live HTTP/fetch/crawl/scrape implementation |
| TASK-006G | Source Change Detection Engine Contract | Complete | Change-detection governance contract only; no diff engine/amendment inference implementation |
| TASK-006H | Controlled Fetch Implementation (Dry-Run + Local Fixture Mode) | Complete | Bounded fetch implementation using dry-run and local fixtures only; no live external fetching |
| TASK-006I | Controlled Fetch Result Persistence | Complete | Append-only fetch request/result persistence with enum/FK governance; no live external fetching or ingestion side effects |
| TASK-006J | Source Change Detection Persistence | Complete | Append-only change-detection request/result persistence with review doctrine validation; no engine implementation |
| TASK-006K | Source Change Detection Engine Skeleton | Complete | Checksum-only detection execution over persisted fetch results; no legal interpretation or source-version creation |
| TASK-006L | Controlled Source Version Promotion Workflow | Complete | Explicit review-gated promotion into canonical source versions with append-only promotion history and duplicate protection |
| TASK-006M | Source Version Extraction Trigger Contract | Complete | Governance-only trigger boundary between canonical source versions and extraction requests; no extraction execution |
| TASK-006N | Extraction Trigger Persistence | Complete | Append-only extraction trigger request/result persistence with deterministic trigger hashes, duplicate protection, and force-reprocess auditability |
| TASK-006O | Extraction Worker Skeleton | Complete | Dry-run-only extraction orchestration from trigger requests to extraction_run lifecycle records; no real extraction or downstream artifact creation |
| TASK-006P | Controlled Extraction Execution | Complete | Controlled local text extraction from approved artifacts into extraction_runs and extracted_texts; no PDF/OCR/network/parsing/legal-object/citation side effects |
| TASK-006P1 | Extraction Replay & Idempotency Hardening | Complete | Verified 2026-06-02; EXT-01/OD-019 remediated; TASK-006Q gate open |
| TASK-006Q | Parsing Trigger Contract | Complete | Governance-only parsing initiation from `extracted_text`; idempotency on `extracted_text_id`; no parsing execution |
| TASK-006R | Parsing Trigger Persistence | Complete | Append-only requests/results, `extracted_text_id` idempotency, DB partial unique index; no parser execution |
| TASK-006S | Parsing Worker Skeleton | Complete | Accepted at `checkpoint-task-006s-parsing-worker-skeleton`; dry-run orchestration only |
| TASK-006T | Controlled Parsing Execution | Complete | Controlled structural parsing into `parsed_structures`; non-interpretive; no legal object/citation/answer |
| TASK-006T1A | Parsed Structure Identity Hardening | Complete | Verified at `checkpoint-task-006t1a-parsed-structure-identity`; P-01/P-02 closed |
| TASK-006U | Legal Object Promotion Contract | Complete | Governance-only `parsed_structure` → `legal_object`; idempotency on `parsed_structure_id` |
| TASK-006V | Legal Object Promotion Persistence | Complete | Append-only requests/results; `parsed_structure_id` idempotency; no promotion execution |
| TASK-006W | Legal Object Promotion Worker Skeleton | Complete | Dry-run orchestration; terminal `skipped`; no legal object creation |
| TASK-006X | Controlled Legal Object Promotion Execution | Complete | Checkpoint `checkpoint-task-006x-controlled-legal-object-promotion-execution`; 633 tests |
| TASK-006X1 | Legal Object Version Identity Hardening | Complete | L-02b verified — `uq_legal_object_versions_object_hash`; no new migration |
| TASK-006Y | Citation Assembly Contract | Complete | Citation governance layer **established**; [`CITATION_ASSEMBLY_CONTRACT.md`](CITATION_ASSEMBLY_CONTRACT.md); complements TASK-004D assembler path |
| TASK-006ZA | Citation Persistence Remediation Package | Complete | Acceptance review **CLOSED**; Z-01–Z-14 remediated; 006Z authorized |
| TASK-006Z | Citation Persistence | Complete | Append-only `citation_assembly_governance_*` tables; Alembic `c6d4f0b15e58`; 667 tests |
| TASK-007A+ | Retrieval & Query Runtime | Planned | After citation persistence; governed query path |
| TASK-DOC-001 | Master Status Document Realignment | Complete | CURRENT_STATUS, IMPLEMENTATION_ROADMAP, ARCHITECTURE_PHASE_MAP |

## Status Legend

| Status | Meaning |
|--------|---------|
| Planned | Approved, not started |
| Hold | Blocked until prerequisite gate closes (e.g. Claude review) |
| Authorized | Approved for implementation; not yet started |
| In progress | Active implementation |
| Pending VM acceptance | Code complete; VM verification required |
| Complete | Accepted per task governance |
| Deferred | Out of current phase |

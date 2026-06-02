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
| TASK-DOC-001 | Master Status Document Realignment | Complete | CURRENT_STATUS, IMPLEMENTATION_ROADMAP, ARCHITECTURE_PHASE_MAP |

## Status Legend

| Status | Meaning |
|--------|---------|
| Planned | Approved, not started |
| In progress | Active implementation |
| Pending VM acceptance | Code complete; VM verification required |
| Complete | Accepted per task governance |
| Deferred | Out of current phase |

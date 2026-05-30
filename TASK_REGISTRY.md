# Task Registry

Bounded task tracking for `tax-os-backend`. Authoritative specs remain in `tax-os-architecture`; this file tracks implementation status.

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

## Status Legend

| Status | Meaning |
|--------|---------|
| Planned | Approved, not started |
| In progress | Active implementation |
| Pending VM acceptance | Code complete; VM verification required |
| Complete | Accepted per task governance |
| Deferred | Out of current phase |

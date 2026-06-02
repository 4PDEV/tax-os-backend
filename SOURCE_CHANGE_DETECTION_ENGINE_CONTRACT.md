# Source Change Detection Engine Contract

## Purpose

Define bounded governance for future source change detection over fetched source artifacts.

This contract is governance-only. It does not authorize implementation of diff algorithms, live fetching, amendment inference, or legal interpretation.

## Change Detection Role

Change detection is responsible for:

- comparing current fetched artifact against prior artifact
- detecting checksum changes
- detecting metadata changes
- detecting content availability changes
- detecting duplicate artifacts
- producing change detection results
- flagging review-required changes

Change detection must not:

- interpret legal amendments
- infer temporal applicability
- infer repeal effect
- create legal objects/citations/answers
- create `source_versions` without review
- publish production knowledge

## Approved Input Boundary

Allowed inputs:

- approved fetch results
- previously stored source artifacts
- monitoring events/candidates
- approved source registry references

Not allowed:

- live fetching
- crawling/scraping
- autonomous discovery

## ChangeDetectionRequest Contract (future)

Required fields:

- `change_detection_request_id`
- `monitoring_candidate_id` (nullable)
- `fetch_result_id` (nullable)
- `source_document_id` (nullable)
- `source_version_id` (nullable)
- `previous_artifact_reference` (nullable)
- `current_artifact_reference`
- `requested_by_actor_type`
- `requested_by_actor_identifier` (nullable)
- `requested_at`
- `detection_reason`
- `notes` (nullable)

## ChangeDetectionResult Contract (future)

Required fields:

- `change_detection_result_id`
- `change_detection_request_id`
- `detection_status`
- `change_detected`
- `change_type`
- `previous_checksum_sha256` (nullable)
- `current_checksum_sha256` (nullable)
- `metadata_diff_json` (nullable)
- `structural_diff_summary` (nullable)
- `confidence`
- `review_required`
- `detector_name`
- `detector_version`
- `detected_at`
- `notes` (nullable)
- `error_category` (nullable)
- `error_message` (nullable)

## Detection Status Values

Allowed `detection_status` values only:

- `pending`
- `completed`
- `failed`
- `skipped`
- `blocked`

## Change Type Values

Allowed `change_type` values only:

- `no_change`
- `checksum_changed`
- `metadata_changed`
- `content_changed`
- `structure_changed`
- `removed_or_unavailable`
- `duplicate_detected`
- `new_artifact`
- `unknown`

## Confidence Values

Allowed `confidence` values only:

- `high`
- `medium`
- `low`

Confidence means detection quality only; it does not imply legal certainty, authority strength, temporal applicability, or amendment significance.

## Review Requirement Doctrine

`review_required = true` is mandatory for:

- `checksum_changed`
- `content_changed`
- `structure_changed`
- `removed_or_unavailable`
- `new_artifact`
- `unknown`

Only `no_change` and deterministic `duplicate_detected` may set `review_required = false`.

## Checksum Comparison Doctrine

SHA-256 is first-level detection:

- same checksum -> no raw-content change detected
- different checksum -> possible content change; review required
- missing checksum -> unknown; review required

Checksum mismatch must not be interpreted as legal amendment.

## Metadata Diff Doctrine

Metadata diffs may include:

- title change
- URL change
- content type change
- content length change
- publication date field change (explicit only)
- issuing authority field change (explicit only)

Metadata differences must remain separate from content change claims.

## Structural Diff Doctrine

Future structural diff may compare:

- sections
- articles
- regulations
- schedules
- paragraphs
- headings
- tables

Allowed example: "Section 12 text changed."
Prohibited example: "Section 12 now denies input VAT recovery."

## Duplicate Detection Doctrine

Duplicate signals may use:

- checksum match
- source URL match
- title/reference similarity
- official reference match where available

Duplicate classification is advisory unless deterministic.

## False Positive Handling

Change detection may generate false positives due to:

- formatting-only changes
- website wrapper changes
- PDF metadata changes
- OCR/extraction differences
- encoding changes
- redirect/URL changes

False positives must be reviewable and auditable.

## Temporal Governance Alignment

Change detection must not infer:

- effective date
- repeal date
- applicability date
- transition date
- legal force
- temporal status

Publication-date differences may be recorded only when explicit and provenance-marked.

## Provenance and Auditability

Every result must preserve:

- prior artifact reference
- current artifact reference
- checksums
- detector version
- detection timestamp
- actor/request context
- detection reason
- `review_required`

No silent mutation is allowed.

## Workflow Relationship

Future governed path:

```text
monitoring candidate
→ controlled fetch
→ fetch result
→ change detection
→ review queue
→ approved source version creation
→ extraction pipeline
```

Prohibited:

```text
change detection
→ automatic source_version creation
```

## Failure Categories

Allowed `error_category` values only:

- `missing_previous_artifact`
- `missing_current_artifact`
- `checksum_unavailable`
- `unsupported_content_type`
- `diff_failed`
- `corrupted_artifact`
- `timeout`
- `unknown_failure`

## Non-Implementation Clause

TASK-006G does not authorize:

- change-detection engine implementation
- diff algorithm implementation
- live fetching/crawling/scraping
- legal/temporal interpretation

## Final Principle

Source change detection says: "Something appears to have changed."
It does not say: "The law has changed."

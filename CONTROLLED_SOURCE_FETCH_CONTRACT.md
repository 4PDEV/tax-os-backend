# Controlled Source Fetch Contract

## Purpose

Define bounded governance for future controlled source fetching from approved official sources.

This contract is governance-only. It does not authorize live HTTP fetching, crawling, scraping, scheduling, queue orchestration, or ingestion automation.

## Fetch Role

Controlled fetch is responsible for:

- retrieving content from approved candidate URLs
- preserving raw source bytes or text
- recording fetch metadata
- computing checksums
- identifying content type
- recording failure reasons
- preparing fetched material for validation/review

Controlled fetch must not:

- approve source authority
- create `source_versions` automatically
- create legal objects
- infer effective/repeal/applicability dates
- interpret legal meaning
- bypass review
- publish production knowledge

## Approved Fetch Boundary

Fetch may operate only on:

- approved monitoring candidates
- approved allowlist entries
- explicitly authorized source URLs
- official or governance-approved sources

Open-ended crawling and autonomous discovery are prohibited.

## FetchRequest Contract (future)

Required fields:

- `fetch_request_id`
- `monitoring_candidate_id` (nullable)
- `source_allowlist_entry_id` (nullable)
- `requested_url`
- `requested_by_actor_type`
- `requested_by_actor_identifier` (nullable)
- `request_reason`
- `requested_at`
- `dry_run`
- `notes` (nullable)

## FetchResult Contract (future)

Required fields:

- `fetch_result_id`
- `fetch_request_id`
- `fetched_url`
- `final_url` (nullable)
- `fetch_status`
- `fetched_at` (nullable)
- `http_status_code` (nullable)
- `content_type` (nullable)
- `content_length` (nullable)
- `checksum_sha256` (nullable)
- `storage_backend` (nullable)
- `storage_path` (nullable)
- `error_category` (nullable)
- `error_message` (nullable)
- `fetcher_name`
- `fetcher_version`

## Fetch Status Values

Allowed `fetch_status` values only:

- `pending`
- `success`
- `failed`
- `blocked`
- `skipped`
- `partial`

## Fetch Error Categories

Allowed `error_category` values only:

- `source_unreachable`
- `access_denied`
- `robots_or_terms_restricted`
- `unsupported_content_type`
- `content_too_large`
- `checksum_failed`
- `timeout`
- `redirect_policy_failed`
- `unexpected_content`
- `unknown_failure`

## Content-Type Discipline

Initially supported future types:

- `application/pdf`
- `text/html`
- `text/plain`
- `application/xml`
- `application/json`

Unsupported types must be recorded as `unsupported_content_type` and must not be silently processed.

## Checksum Discipline

Every successful fetch must compute SHA-256 over canonical raw content bytes.

Checksum is required for:

- change detection
- duplicate detection
- integrity verification
- audit reproducibility

## Storage Discipline

Fetched content must be immutable raw artifact storage.

Potential future backends:

- database
- local filesystem
- S3
- MinIO
- Azure Blob

Storage implementation is out of scope for TASK-006F.

## Redirect Governance

- record `final_url`
- bound redirect chains
- block redirects to unapproved domains unless explicitly allowed
- record `redirect_policy_failed` on blocked redirect paths

## Robots / Terms / Licensing Discipline

Fetching must respect:

- robots restrictions where applicable
- website terms where applicable
- licensing restrictions
- paywall/access constraints
- official-source usage conditions

If restricted:

- `fetch_status = blocked`
- `error_category = robots_or_terms_restricted`

## Rate Limit / Backoff Doctrine

Future fetchers must support:

- rate limiting
- retry caps
- exponential or fixed backoff
- no aggressive polling
- no denial-of-service behavior

Doctrine only in TASK-006F.

## Temporal Governance Alignment

Fetch may record only explicitly available metadata.

Fetch must not infer:

- effective date
- applicability date
- repeal date
- legal force
- temporal status

Publication dates may be recorded only when explicit and provenance-marked.

## Review-Before-Ingestion Rule

Fetched material must not automatically create:

- `source_versions`
- `extracted_texts`
- `legal_objects`
- citations
- answers

Workflow remains:

```text
candidate
→ fetch request
→ fetch result
→ validation/review
→ approved source version creation
→ extraction pipeline
```

## Auditability

Every future fetch attempt must preserve:

- request actor
- requested URL
- source candidate context
- timestamp
- fetcher version
- result status
- checksum
- storage location
- error category when failed

## Security Constraints

Contract-level requirements:

- URL validation
- scheme restrictions
- SSRF protections
- internal/private IP blocking
- max content size limits
- timeout limits
- redirect limits

## Non-Implementation Clause

TASK-006F authorizes governance only, not live implementation.

No external website access is permitted in this task.

## Final Principle

Controlled fetch obtains source material; it does not determine legal truth, authority, interpretation, or applicability.

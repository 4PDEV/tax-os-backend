# Source Monitoring Agent Contract

## Purpose

Define bounded governance for source monitoring agents in the Source-Referenced Business & Tax Research Platform.

This contract is detection-oriented only. It does not authorize live scraping, schedulers, crawlers, or autonomous publishing.

## Scope Boundary

Source Monitoring Agents are:

- acquisition assistants
- detection systems
- candidate generators

Source Monitoring Agents are not:

- legal interpreters
- authority resolvers
- ingestion approvers
- production truth engines

## Explicitly Allowed

- Check approved source locations.
- Detect candidate changes.
- Detect new documents.
- Detect modified documents.
- Detect missing or unavailable documents.
- Capture retrieval metadata.
- Generate monitoring events.
- Create candidate review items.

## Explicitly Prohibited

- Production publishing.
- Legal interpretation.
- Legal object creation.
- Automatic ingestion approval.
- Authority ranking.
- Temporal inference.
- Silent source replacement.
- Review workflow bypass.

## Approved Source Boundary

Authoritative monitoring categories:

- official government websites
- official gazettes
- official tax authority portals
- official court or tribunal portals
- approved treaty repositories
- approved accounting-standard repositories where permitted

Non-approved sources can only be informational leads and must never become authoritative ingestion sources automatically.

## Source Allowlist Contract (future model)

Defined now for governance; persistence implementation is out of scope for TASK-006C.

- `source_allowlist_id`
- `jurisdiction`
- `authority_name`
- `source_type`
- `base_url`
- `allowed_patterns`
- `blocked_patterns`
- `monitoring_frequency`
- `status`
- `notes`
- `created_at`
- `updated_at`

## Monitoring Event Contract

Canonical event shape:

- `monitoring_event_id`
- `source_registry_id` (nullable)
- `source_url`
- `source_name`
- `source_type`
- `detected_title`
- `detected_url`
- `detected_at`
- `detection_method`
- `checksum_sha256` (nullable)
- `previous_checksum_sha256` (nullable)
- `change_type`
- `candidate_state`
- `confidence`
- `notes`
- `agent_name`
- `agent_version`

## Change Type Contract

Allowed `change_type` values only:

- `new_document`
- `modified_document`
- `removed_or_unavailable`
- `metadata_changed`
- `checksum_changed`
- `unknown`

No implicit or hidden values are permitted.

## Candidate State Contract

Allowed `candidate_state` values only:

- `detected`
- `queued_for_review`
- `rejected`
- `approved_for_ingestion`
- `superseded`
- `failed`

These states are monitoring candidate states only and are explicitly separate from:

- `source_versions.version_status`
- legal object lifecycle status
- ingestion persistence state
- temporal state

## Confidence Contract

Allowed `confidence` values only:

- `high`
- `medium`
- `low`

Confidence is detection quality only. It is not legal certainty, authority strength, or temporal applicability.

## Monitoring Workflow Governance

Governed flow:

```text
approved source
→ monitoring check
→ monitoring event
→ candidate review queue
→ validation/review
→ approved ingestion
→ extraction pipeline
```

Prohibited flow:

```text
monitoring event
→ direct production source update
```

## Temporal Governance Alignment

Monitoring agents may record publication dates only when explicitly present in source material.

Monitoring agents must never infer:

- effective dates
- repeal dates
- applicability dates
- temporal status
- legal force

## Failure Handling Contract

Allowed failure categories:

- `source_unreachable`
- `access_denied`
- `robots_or_terms_restricted`
- `parse_failed`
- `checksum_failed`
- `unexpected_content`
- `timeout`
- `unknown_failure`

Failures must remain observable, auditable, and never silent.

## Logging and Audit Expectations

Future monitoring attempts should preserve:

- source checked
- timestamp
- outcome
- checksum result
- errors
- agent version
- candidate creation result

## Security and Governance Constraints

- Monitoring must obey robots and terms where applicable.
- Monitoring must remain rate-limited.
- Monitoring scope must remain allowlist-driven.
- Source expansion requires governance approval.

## Non-Implementation Clause

TASK-006C authorizes contract and governance only.

TASK-006C does not authorize:

- live agents
- schedulers
- crawlers
- scraping
- external traffic
- queue implementation
- persistence table implementation
- ingestion approval automation

## Final Principle

Source Monitoring Agents detect possible source changes.

They do not determine legal meaning, legal authority, temporal applicability, legal truth, or production publication state.

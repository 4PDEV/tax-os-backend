# TASK-006C — Source Monitoring Agent Contract

## Status

APPROVED FOR IMPLEMENTATION

## Objective

Define bounded governance and operational contracts for Source Monitoring Agents.

This task is contract and governance only.

## Scope

Establish:

- monitoring-agent scope
- monitoring-event contracts
- source-boundary governance
- candidate-review workflow
- monitoring-state discipline
- failure handling
- temporal no-inference alignment

No live agents, external traffic, schedulers, crawlers, or scraping are permitted in this task.

## Canonical Contract

Primary specification:

- `SOURCE_MONITORING_AGENT_CONTRACT.md`

This file records task governance acceptance and implementation boundaries.

## Accepted Governance Statements

1. Monitoring agents are acquisition assistants and candidate generators, not legal interpreters.
2. Monitoring events cannot directly publish to production source truth.
3. Candidate states and confidence values are namespaced for monitoring only.
4. Monitoring does not infer legal meaning or temporal applicability.
5. Allowlist governance controls source scope expansion.
6. Failures must remain auditable and non-silent.

## Contracted Value Sets

### Change types

- `new_document`
- `modified_document`
- `removed_or_unavailable`
- `metadata_changed`
- `checksum_changed`
- `unknown`

### Candidate states

- `detected`
- `queued_for_review`
- `rejected`
- `approved_for_ingestion`
- `superseded`
- `failed`

### Confidence

- `high`
- `medium`
- `low`

### Failure categories

- `source_unreachable`
- `access_denied`
- `robots_or_terms_restricted`
- `parse_failed`
- `checksum_failed`
- `unexpected_content`
- `timeout`
- `unknown_failure`

## Workflow Contract

```text
approved source
→ monitoring check
→ monitoring event
→ candidate review queue
→ validation/review
→ approved ingestion
→ extraction pipeline
```

Prohibited:

```text
monitoring event
→ direct production source update
```

## Out of Scope

- live monitoring agents
- crawling, scraping, schedulers
- persistence implementation
- queue implementation
- ingestion approval automation
- legal interpretation
- temporal inference

## Acceptance

TASK-006C is complete when:

- contract exists in canonical repo docs
- monitoring boundaries are explicit
- values/states are explicit and bounded
- no implementation scope creep is introduced

## Final Principle

Monitoring identifies candidate change. Human and governed workflows decide production truth.

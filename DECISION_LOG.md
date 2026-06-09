# DECISION LOG

---

## DEC-001
LLMs must never answer tax or legal questions directly from model memory.

Status:
LOCKED

---

## DEC-002
All production answers must be source-referenced.

Status:
LOCKED

---

## DEC-003
Legal objects and source versions must never be silently overwritten.

Status:
LOCKED

---

## DEC-004
The platform must be effective-date-aware and version-aware.

Status:
LOCKED

---

## DEC-005
The system must surface ambiguity, conflicts, uncertainty, and risk rather than pretending certainty.

Status:
LOCKED

---

## DEC-006
Architecture authority remains centralized and governed.

Status:
LOCKED

---

## DEC-007
Development must occur through bounded tasks only.

Status:
LOCKED

---

## DEC-008
Agents may retrieve and structure information but may not autonomously publish production truth.

Status:
LOCKED

---

## DEC-009
The platform shall evolve progressively:
- country by country
- tax regime by tax regime
- module by module

Status:
LOCKED

---

## DEC-010
Ranking stores order only. Provenance lives once in `retrieval_evidence_references`. `ranked_evidence_references` are pure pointers (`retrieval_result_id`, `retrieval_evidence_reference_id`, `presentation_order_index`) — no copied provenance fields.

Authority: TASK-008C-REMEDIATION — [`RANKING_PERSISTENCE_REMEDIATION_008C-REMEDIATION.md`](RANKING_PERSISTENCE_REMEDIATION_008C-REMEDIATION.md); verified TASK-008C-PREAUTH-RECONCILIATION — [`TASKS/TASK-008C-PREAUTH-RECONCILIATION.md`](TASKS/TASK-008C-PREAUTH-RECONCILIATION.md)

Status:
LOCKED

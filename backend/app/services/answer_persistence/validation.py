REQUESTED_BY_ACTOR_TYPES = {"user", "system", "worker", "admin", "test"}
ANSWER_STATUSES = {
    "pending",
    "accepted",
    "completed",
    "failed",
    "skipped",
    "duplicate_rejected",
}
ANSWER_ERROR_CATEGORIES = {
    "ranking_result_not_completed",
    "accepted_ranking_result_missing",
    "ranked_evidence_missing",
    "evidence_count_mismatch",
    "provenance_chain_incomplete",
    "citation_reference_incomplete",
    "retrieval_result_mismatch",
    "assembly_validation_failed",
    "answer_pipeline_unavailable",
    "unknown_failure",
    "duplicate_answer",
    "ranking_request_missing",
    "invalid_answer_request",
}
PROHIBITED_ERROR_CATEGORIES = {
    "permutation_mismatch",
    "duplicate_ranking",
    "retrieval_result_missing",
    "profile_not_allowed",
    "ranking_pipeline_unavailable",
}
UNCERTAINTY_FLAG_TYPES = {
    "conflict",
    "ambiguity",
    "incomplete_provenance",
    "zero_evidence",
    "other",
}
UNCERTAINTY_SEVERITIES = {"informational", "warning", "error"}

ANSWER_EVIDENCE_ALLOWED_COLUMNS = {
    "id",
    "answer_result_id",
    "answer_request_id",
    "ranking_request_id",
    "ranked_evidence_reference_id",
    "retrieval_result_id",
    "retrieval_evidence_reference_id",
    "presentation_order_index",
    "created_at",
}

PROHIBITED_TABLE_COLUMNS = {
    "legal_object_id",
    "legal_object_version_id",
    "source_version_id",
    "source_document_id",
    "citation_id",
    "citation_hash",
    "rendered_citation_text",
    "answer_text",
    "legal_conclusion",
    "recommendation_text",
    "ranking_score",
    "relevance_score",
    "confidence_score",
    "semantic_score",
    "ai_score",
    "object_identifier",
    "location_reference",
    "evidence_metadata",
    "deterministic_order_index",
}

TERMINAL_ANSWER_STATUSES = frozenset(
    {"completed", "failed", "skipped", "duplicate_rejected"}
)


def validate_actor_type(actor_type: str) -> None:
    if actor_type not in REQUESTED_BY_ACTOR_TYPES:
        raise ValueError(f"invalid requested_by_actor_type: {actor_type}")


def validate_answer_status(answer_status: str) -> None:
    if answer_status not in ANSWER_STATUSES:
        raise ValueError(f"invalid answer_status: {answer_status}")


def validate_answer_error_category(error_category: str | None) -> None:
    if error_category is None:
        return
    if error_category in PROHIBITED_ERROR_CATEGORIES:
        raise ValueError(f"prohibited error_category: {error_category}")
    if error_category not in ANSWER_ERROR_CATEGORIES:
        raise ValueError(f"invalid error_category: {error_category}")


def validate_uncertainty_flag_type(flag_type: str) -> None:
    if flag_type not in UNCERTAINTY_FLAG_TYPES:
        raise ValueError(f"invalid flag_type: {flag_type}")


def validate_uncertainty_severity(severity: str) -> None:
    if severity not in UNCERTAINTY_SEVERITIES:
        raise ValueError(f"invalid severity: {severity}")

RANKING_PROFILES = {
    "CANONICAL",
    "EFFECTIVE_DATE_DESC",
    "GROUP_BY_SOURCE",
    "GROUP_BY_DOCUMENT",
}
REQUESTED_BY_ACTOR_TYPES = {"user", "system", "worker", "admin", "test"}
RANKING_STATUSES = {
    "pending",
    "accepted",
    "completed",
    "failed",
    "skipped",
    "duplicate_rejected",
}
RANKING_ERROR_CATEGORIES = {
    "retrieval_result_missing",
    "retrieval_result_not_completed",
    "evidence_reference_missing",
    "provenance_incomplete",
    "profile_not_allowed",
    "duplicate_ranking",
    "permutation_mismatch",
    "ranking_pipeline_unavailable",
    "unknown_failure",
}
PROHIBITED_ERROR_CATEGORIES = {
    "evidence_set_empty",
    "invalid_request",
    "retrieval_not_completed",
    "permutation_violation",
}

RANKED_EVIDENCE_ALLOWED_COLUMNS = {
    "id",
    "ranking_result_id",
    "retrieval_result_id",
    "retrieval_evidence_reference_id",
    "presentation_order_index",
    "created_at",
}

PROHIBITED_TABLE_COLUMNS = {
    "legal_object_id",
    "legal_object_version_id",
    "source_version_id",
    "citation_id",
    "citation_hash",
    "source_document_id",
    "answer_text",
    "legal_conclusion",
    "applicability_flag",
    "authority_weight",
    "importance_flag",
    "preference_score",
    "ranking_score",
    "relevance_score",
    "confidence_score",
    "semantic_score",
    "ai_score",
    "llm_score",
    "bm25_score",
    "recommendation_text",
    "summary_text",
    "deterministic_order_index",
}


def validate_ranking_profile(ranking_profile: str) -> None:
    if ranking_profile not in RANKING_PROFILES:
        raise ValueError(f"invalid ranking_profile: {ranking_profile}")


def validate_actor_type(actor_type: str) -> None:
    if actor_type not in REQUESTED_BY_ACTOR_TYPES:
        raise ValueError(f"invalid requested_by_actor_type: {actor_type}")


def validate_ranking_status(ranking_status: str) -> None:
    if ranking_status not in RANKING_STATUSES:
        raise ValueError(f"invalid ranking_status: {ranking_status}")


def validate_ranking_error_category(error_category: str | None) -> None:
    if error_category is None:
        return
    if error_category in PROHIBITED_ERROR_CATEGORIES:
        raise ValueError(f"prohibited error_category: {error_category}")
    if error_category not in RANKING_ERROR_CATEGORIES:
        raise ValueError(f"invalid error_category: {error_category}")

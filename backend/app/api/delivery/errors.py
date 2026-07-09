"""API delivery error vocabulary and HTTP status mapping (TASK-011A)."""

API_ERROR_CODES = frozenset(
    {
        "invalid_request",
        "unsupported_api_version",
        "unsupported_contract_version",
        "answer_request_not_found",
        "answer_result_not_found",
        "answer_not_ready",
        "answer_not_deliverable",
        "delivery_incomplete",
        "service_unavailable",
    }
)

# Runtime error_category → API error_code (D-A-08)
RUNTIME_TO_API_ERROR_CODE: dict[str, str] = {
    "invalid_response_request": "invalid_request",
    "contract_version_unsupported": "unsupported_contract_version",
    "answer_request_not_found": "answer_request_not_found",
    "answer_result_not_found": "answer_result_not_found",
    "answer_not_completed": "answer_not_ready",
    "answer_not_deliverable": "answer_not_deliverable",
    "accepted_result_missing": "delivery_incomplete",
    "evidence_count_mismatch": "delivery_incomplete",
    "provenance_resolution_failed": "delivery_incomplete",
    "citation_format_failed": "delivery_incomplete",
    "response_pipeline_unavailable": "service_unavailable",
}

# API error_code → HTTP status (D-A-07)
API_ERROR_HTTP_STATUS: dict[str, int] = {
    "invalid_request": 400,
    "unsupported_api_version": 400,
    "unsupported_contract_version": 400,
    "answer_request_not_found": 404,
    "answer_result_not_found": 404,
    "answer_not_ready": 409,
    "answer_not_deliverable": 409,
    "delivery_incomplete": 503,
    "service_unavailable": 503,
}

DEFAULT_API_ERROR_CODE = "service_unavailable"
HTTP_STATUS_SUCCESS = 200


def translate_runtime_error_category(error_category: str | None) -> str:
    """Map runtime error_category to API-only error_code. Never return raw runtime category."""
    if error_category is None:
        return DEFAULT_API_ERROR_CODE
    return RUNTIME_TO_API_ERROR_CODE.get(error_category, DEFAULT_API_ERROR_CODE)


def http_status_for_api_error(error_code: str) -> int:
    return API_ERROR_HTTP_STATUS.get(error_code, API_ERROR_HTTP_STATUS[DEFAULT_API_ERROR_CODE])

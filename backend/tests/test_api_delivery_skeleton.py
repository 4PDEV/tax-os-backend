"""TASK-011A API delivery skeleton tests."""

from pathlib import Path
from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

import pytest

from app.api import delivery as delivery_pkg
from app.api.delivery import (
    CURRENT_API_CONTRACT_VERSION,
    ApiDeliveryError,
    ApiDeliveryMetadata,
    ApiDeliveryOutcome,
    ApiDeliveryRequest,
    build_api_delivery_response,
)
from app.api.delivery.errors import (
    API_ERROR_CODES,
    API_ERROR_HTTP_STATUS,
    RUNTIME_TO_API_ERROR_CODE,
    http_status_for_api_error,
    translate_runtime_error_category,
)
from app.api.delivery.mapper import map_to_response_request, validate_api_delivery_request
from app.api.delivery.models import API_TO_RUNTIME_CONTRACT_VERSION
from app.services.response_runtime import (
    RESPONSE_STATUS_COMPLETED,
    RESPONSE_STATUS_FAILED,
    ResponseCitationReference,
    ResponseEvidenceEntry,
    ResponseMetadata,
    ResponseOutcome,
    ResponsePackage,
    ResponseRequest,
    ResponseRuntimeError,
    ResponseUncertaintyFlag,
)

DELIVERY_DIR = Path(__file__).resolve().parents[1] / "app" / "api" / "delivery"

PROHIBITED_IMPORT_TOKENS = (
    "app.services.retrieval_execution",
    "app.services.ranking_execution",
    "app.workers.ranking_runtime",
    "app.workers.retrieval_runtime",
    "app.workers.answer_runtime",
    "app.services.answer_assembly",
    "app.services.answer_persistence",
    "create_answer_request",
    "create_answer_result",
    "persist_answer_for_ranking_request",
    "assemble_answer_package",
    "resolve_ranking_assembly_inputs",
    "run_answer_worker",
    "run_ranking_worker",
    "CitationFormatter",
    "CitationAssembler",
    "app.services.citation.assembler",
    "app.services.ai",
    "app.services.semantic",
    "app.services.vector",
    "fastapi",
    "APIRouter",
    "app.api.routes",
    "celery",
    "redis",
    "rabbitmq",
    "kafka",
)

AUTHORIZED_FILES = frozenset({"__init__.py", "models.py", "mapper.py", "errors.py"})


def _package(
    *,
    answer_request_id: UUID,
    answer_result_id: UUID,
    response_metadata: ResponseMetadata | None = None,
    evidence_count: int = 1,
) -> ResponsePackage:
    evidence = []
    for index in range(1, evidence_count + 1):
        evidence.append(
            ResponseEvidenceEntry(
                presentation_order_index=index,
                retrieval_evidence_reference_id=uuid4(),
                ranked_evidence_reference_id=uuid4(),
                legal_object_id=f"lo-{index}",
                source_version_id=uuid4(),
                object_identifier=f"obj-{index}",
                location_reference=f"loc-{index}",
                citation_reference=ResponseCitationReference(
                    citation_id=f"cit-{index}",
                    citation_hash=f"hash-{index}",
                    rendered_citation_text=None,
                ),
                entry_metadata=None,
            )
        )
    return ResponsePackage(
        contract_version="010A-v1",
        answer_request_id=answer_request_id,
        answer_result_id=answer_result_id,
        rank_count=evidence_count,
        evidence_entries=evidence,
        uncertainty_flags=[
            ResponseUncertaintyFlag(
                flag_type="zero_evidence" if evidence_count == 0 else "other",
                severity="informational",
                message="note",
                related_evidence_ids=[],
            )
        ],
        response_metadata=response_metadata,
    )


def test_delivery_package_has_only_authorized_modules():
    names = {path.name for path in DELIVERY_DIR.glob("*.py")}
    assert names == AUTHORIZED_FILES


def test_public_exports_single_callable_only():
    """Finding 4 hardening: __all__ exposes one callable; rest are DTOs/constants."""
    expected = {
        "CURRENT_API_CONTRACT_VERSION",
        "DELIVERY_STATUS_COMPLETED",
        "DELIVERY_STATUS_FAILED",
        "ApiDeliveryCitationReference",
        "ApiDeliveryError",
        "ApiDeliveryEvidenceEntry",
        "ApiDeliveryMetadata",
        "ApiDeliveryOutcome",
        "ApiDeliveryRequest",
        "ApiDeliveryResponse",
        "ApiDeliveryUncertaintyFlag",
        "build_api_delivery_response",
    }
    assert set(delivery_pkg.__all__) == expected
    callables = [
        name
        for name in delivery_pkg.__all__
        if callable(getattr(delivery_pkg, name)) and not isinstance(getattr(delivery_pkg, name), type)
    ]
    assert callables == ["build_api_delivery_response"]


def test_delivery_import_guards():
    sources = []
    for path in sorted(DELIVERY_DIR.glob("*.py")):
        sources.append(path.read_text(encoding="utf-8").lower())
    joined = "\n".join(sources)
    for token in PROHIBITED_IMPORT_TOKENS:
        assert token.lower() not in joined, f"{token} must not appear in api/delivery"


def test_validate_api_delivery_request_accepts_valid_envelope():
    request = ApiDeliveryRequest(answer_request_id=uuid4())
    assert validate_api_delivery_request(request) is None


def test_validate_rejects_unsupported_api_version():
    request = ApiDeliveryRequest(
        answer_request_id=uuid4(),
        api_contract_version="999A-v9",
    )
    assert validate_api_delivery_request(request) == "unsupported_api_version"


def test_validate_rejects_non_uuid_answer_request_id():
    request = ApiDeliveryRequest(answer_request_id="not-a-uuid")  # type: ignore[arg-type]
    assert validate_api_delivery_request(request) == "invalid_request"


def test_map_to_response_request_version_011a_to_010a():
    answer_request_id = uuid4()
    answer_result_id = uuid4()
    api_request = ApiDeliveryRequest(
        answer_request_id=answer_request_id,
        api_contract_version=CURRENT_API_CONTRACT_VERSION,
        include_rendered_citation_text=True,
        answer_result_id=answer_result_id,
    )
    mapped = map_to_response_request(api_request)
    assert isinstance(mapped, ResponseRequest)
    assert mapped.answer_request_id == answer_request_id
    assert mapped.answer_result_id == answer_result_id
    assert mapped.include_rendered_citation_text is True
    assert mapped.contract_version == "010A-v1"
    assert mapped.contract_version == API_TO_RUNTIME_CONTRACT_VERSION["011A-v1"]
    assert mapped.contract_version != "011A-v1"


def test_build_api_delivery_response_unsupported_version_does_not_call_runtime():
    db = MagicMock()
    request = ApiDeliveryRequest(
        answer_request_id=uuid4(),
        api_contract_version="bad-version",
    )
    with patch("app.api.delivery.mapper.build_response") as mock_build:
        outcome = build_api_delivery_response(db, request)
    mock_build.assert_not_called()
    assert outcome.http_status == 400
    assert outcome.response.delivery_status == "failed"
    assert outcome.response.error is not None
    assert isinstance(outcome.response.error, ApiDeliveryError)
    assert outcome.response.error.error_code == "unsupported_api_version"
    assert outcome.response.evidence_entries is None


def test_success_mapping_and_nested_error_is_none():
    db = MagicMock()
    answer_request_id = uuid4()
    answer_result_id = uuid4()
    metadata = ResponseMetadata(
        rendering_mode="deterministic",
        include_rendered_citation_text=False,
        notes="n1",
    )
    package = _package(
        answer_request_id=answer_request_id,
        answer_result_id=answer_result_id,
        response_metadata=metadata,
        evidence_count=2,
    )
    runtime_outcome = ResponseOutcome(
        response_status=RESPONSE_STATUS_COMPLETED,
        response_package=package,
    )
    request = ApiDeliveryRequest(answer_request_id=answer_request_id)

    with patch("app.api.delivery.mapper.build_response", return_value=runtime_outcome) as mock_build:
        outcome = build_api_delivery_response(db, request)

    mock_build.assert_called_once()
    called_request = mock_build.call_args.args[1]
    assert called_request.contract_version == "010A-v1"

    assert outcome.http_status == 200
    assert outcome.response.delivery_status == "completed"
    assert outcome.response.api_contract_version == "011A-v1"
    assert outcome.response.answer_request_id == answer_request_id
    assert outcome.response.answer_result_id == answer_result_id
    assert outcome.response.rank_count == 2
    assert outcome.response.evidence_entries is not None
    assert len(outcome.response.evidence_entries) == 2
    assert outcome.response.evidence_entries[0].presentation_order_index == 1
    assert outcome.response.evidence_entries[1].presentation_order_index == 2
    assert outcome.response.delivery_metadata == ApiDeliveryMetadata(
        rendering_mode="deterministic",
        include_rendered_citation_text=False,
        notes="n1",
    )
    assert outcome.response.error is None


def test_delivery_metadata_null_when_response_metadata_null():
    db = MagicMock()
    answer_request_id = uuid4()
    package = _package(
        answer_request_id=answer_request_id,
        answer_result_id=uuid4(),
        response_metadata=None,
    )
    runtime_outcome = ResponseOutcome(
        response_status=RESPONSE_STATUS_COMPLETED,
        response_package=package,
    )
    with patch("app.api.delivery.mapper.build_response", return_value=runtime_outcome):
        outcome = build_api_delivery_response(
            db,
            ApiDeliveryRequest(answer_request_id=answer_request_id),
        )
    assert outcome.response.delivery_metadata is None


def test_delivery_metadata_never_synthesizes_empty_object():
    db = MagicMock()
    answer_request_id = uuid4()
    package = _package(
        answer_request_id=answer_request_id,
        answer_result_id=uuid4(),
        response_metadata=None,
    )
    runtime_outcome = ResponseOutcome(
        response_status=RESPONSE_STATUS_COMPLETED,
        response_package=package,
    )
    with patch("app.api.delivery.mapper.build_response", return_value=runtime_outcome):
        outcome = build_api_delivery_response(
            db,
            ApiDeliveryRequest(answer_request_id=answer_request_id),
        )
    assert outcome.response.delivery_metadata is None
    assert outcome.response.delivery_metadata is not False  # explicit None, not falsy object


@pytest.mark.parametrize(
    ("runtime_category", "api_code", "http_status"),
    [
        ("answer_not_completed", "answer_not_ready", 409),
        ("answer_not_deliverable", "answer_not_deliverable", 409),
        ("answer_request_not_found", "answer_request_not_found", 404),
        ("answer_result_not_found", "answer_result_not_found", 404),
        ("invalid_response_request", "invalid_request", 400),
        ("contract_version_unsupported", "unsupported_contract_version", 400),
        ("accepted_result_missing", "delivery_incomplete", 503),
        ("evidence_count_mismatch", "delivery_incomplete", 503),
        ("provenance_resolution_failed", "delivery_incomplete", 503),
        ("citation_format_failed", "delivery_incomplete", 503),
        ("response_pipeline_unavailable", "service_unavailable", 503),
        ("unknown_runtime_category", "service_unavailable", 503),
    ],
)
def test_runtime_failure_mapping_table(runtime_category, api_code, http_status):
    db = MagicMock()
    answer_request_id = uuid4()
    runtime_outcome = ResponseOutcome(
        response_status=RESPONSE_STATUS_FAILED,
        response_package=None,
        error_category=runtime_category,
        error_message=f"msg:{runtime_category}",
    )
    with patch("app.api.delivery.mapper.build_response", return_value=runtime_outcome):
        outcome = build_api_delivery_response(
            db,
            ApiDeliveryRequest(answer_request_id=answer_request_id),
        )
    assert outcome.http_status == http_status
    assert outcome.response.delivery_status == "failed"
    assert outcome.response.error is not None
    assert outcome.response.error.error_code == api_code
    assert outcome.response.error.error_message == f"msg:{runtime_category}"
    assert outcome.response.error.error_code in API_ERROR_CODES
    field_names = set(outcome.response.__dataclass_fields__)
    assert "error" in field_names
    assert "error_code" not in field_names
    assert "error_message" not in field_names


def test_409_tradeoff_distinguished_by_error_code():
    db = MagicMock()
    answer_request_id = uuid4()

    not_ready = ResponseOutcome(
        response_status=RESPONSE_STATUS_FAILED,
        response_package=None,
        error_category="answer_not_completed",
        error_message="not completed",
    )
    not_deliverable = ResponseOutcome(
        response_status=RESPONSE_STATUS_FAILED,
        response_package=None,
        error_category="answer_not_deliverable",
        error_message="not deliverable",
    )

    with patch("app.api.delivery.mapper.build_response", return_value=not_ready):
        a = build_api_delivery_response(db, ApiDeliveryRequest(answer_request_id=answer_request_id))
    with patch("app.api.delivery.mapper.build_response", return_value=not_deliverable):
        b = build_api_delivery_response(db, ApiDeliveryRequest(answer_request_id=answer_request_id))

    assert a.http_status == 409
    assert b.http_status == 409
    assert a.response.error is not None and b.response.error is not None
    assert a.response.error.error_code == "answer_not_ready"
    assert b.response.error.error_code == "answer_not_deliverable"
    assert a.response.error.error_code != b.response.error.error_code


def test_response_runtime_error_exception_mapped():
    db = MagicMock()
    answer_request_id = uuid4()
    with patch(
        "app.api.delivery.mapper.build_response",
        side_effect=ResponseRuntimeError(
            "answer_not_completed",
            error_category="answer_not_completed",
        ),
    ):
        outcome = build_api_delivery_response(
            db,
            ApiDeliveryRequest(answer_request_id=answer_request_id),
        )
    assert outcome.http_status == 409
    assert outcome.response.error is not None
    assert outcome.response.error.error_code == "answer_not_ready"


def test_unexpected_exception_maps_to_service_unavailable():
    db = MagicMock()
    answer_request_id = uuid4()
    with patch(
        "app.api.delivery.mapper.build_response",
        side_effect=RuntimeError("boom"),
    ):
        outcome = build_api_delivery_response(
            db,
            ApiDeliveryRequest(answer_request_id=answer_request_id),
        )
    assert outcome.http_status == 503
    assert outcome.response.error is not None
    assert outcome.response.error.error_code == "service_unavailable"


def test_determinism_same_inputs_same_outcome():
    db = MagicMock()
    answer_request_id = uuid4()
    answer_result_id = uuid4()
    package = _package(
        answer_request_id=answer_request_id,
        answer_result_id=answer_result_id,
        response_metadata=ResponseMetadata(
            rendering_mode="deterministic",
            include_rendered_citation_text=True,
            notes=None,
        ),
        evidence_count=1,
    )
    runtime_outcome = ResponseOutcome(
        response_status=RESPONSE_STATUS_COMPLETED,
        response_package=package,
    )
    request = ApiDeliveryRequest(
        answer_request_id=answer_request_id,
        include_rendered_citation_text=True,
    )
    with patch("app.api.delivery.mapper.build_response", return_value=runtime_outcome):
        first = build_api_delivery_response(db, request)
        second = build_api_delivery_response(db, request)
    assert first == second


def test_translate_runtime_error_category_never_leaks_unknown():
    assert translate_runtime_error_category("answer_not_completed") == "answer_not_ready"
    assert translate_runtime_error_category("totally_unknown") == "service_unavailable"
    assert translate_runtime_error_category(None) == "service_unavailable"
    for runtime_code, api_code in RUNTIME_TO_API_ERROR_CODE.items():
        assert api_code in API_ERROR_CODES
        assert http_status_for_api_error(api_code) == API_ERROR_HTTP_STATUS[api_code]
        assert runtime_code != api_code or api_code in {
            "answer_request_not_found",
            "answer_result_not_found",
            "answer_not_deliverable",
        }


def test_nested_error_shape_on_failure():
    db = MagicMock()
    answer_request_id = uuid4()
    runtime_outcome = ResponseOutcome(
        response_status=RESPONSE_STATUS_FAILED,
        response_package=None,
        error_category="answer_not_deliverable",
        error_message="failed terminal",
    )
    with patch("app.api.delivery.mapper.build_response", return_value=runtime_outcome):
        outcome = build_api_delivery_response(
            db,
            ApiDeliveryRequest(answer_request_id=answer_request_id),
        )
    assert isinstance(outcome, ApiDeliveryOutcome)
    assert isinstance(outcome.response.error, ApiDeliveryError)
    field_names = set(outcome.response.__dataclass_fields__)
    assert "error" in field_names
    assert "error_code" not in field_names
    assert "error_message" not in field_names


def test_skeleton_avoids_http_client_frameworks():
    source = Path(__file__).read_text(encoding="utf-8")
    # Scan import lines only — avoid matching this function's own name.
    import_lines = [
        line.strip().lower()
        for line in source.splitlines()
        if line.strip().startswith(("import ", "from "))
    ]
    joined = "\n".join(import_lines)
    assert "fastapi" not in joined
    assert "httpx" not in joined
    assert "starlette" not in joined
    assert "testclient" not in joined

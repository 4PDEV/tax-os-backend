"""API delivery mapping — sole entry build_api_delivery_response (TASK-011A)."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.api.delivery.errors import (
    HTTP_STATUS_SUCCESS,
    http_status_for_api_error,
    translate_runtime_error_category,
)
from app.api.delivery.models import (
    API_TO_RUNTIME_CONTRACT_VERSION,
    CURRENT_API_CONTRACT_VERSION,
    DELIVERY_STATUS_COMPLETED,
    DELIVERY_STATUS_FAILED,
    SUPPORTED_API_CONTRACT_VERSIONS,
    ApiDeliveryCitationReference,
    ApiDeliveryError,
    ApiDeliveryEvidenceEntry,
    ApiDeliveryMetadata,
    ApiDeliveryOutcome,
    ApiDeliveryRequest,
    ApiDeliveryResponse,
    ApiDeliveryUncertaintyFlag,
)
from app.services.response_runtime import (
    RESPONSE_STATUS_COMPLETED,
    ResponseMetadata,
    ResponseOutcome,
    ResponsePackage,
    ResponseRequest,
    ResponseRuntimeError,
    build_response,
)


def _failed_outcome(
    *,
    answer_request_id: UUID,
    error_code: str,
    error_message: str | None,
) -> ApiDeliveryOutcome:
    return ApiDeliveryOutcome(
        http_status=http_status_for_api_error(error_code),
        response=ApiDeliveryResponse(
            api_contract_version=CURRENT_API_CONTRACT_VERSION,
            delivery_status=DELIVERY_STATUS_FAILED,
            answer_request_id=answer_request_id,
            answer_result_id=None,
            rank_count=None,
            evidence_entries=None,
            uncertainty_flags=None,
            delivery_metadata=None,
            error=ApiDeliveryError(
                error_code=error_code,
                error_message=error_message,
            ),
        ),
    )


def validate_api_delivery_request(request: ApiDeliveryRequest) -> str | None:
    """Return API error_code on validation failure, else None."""
    if not isinstance(request.answer_request_id, UUID):
        return "invalid_request"
    if not request.api_contract_version:
        return "invalid_request"
    if request.api_contract_version not in SUPPORTED_API_CONTRACT_VERSIONS:
        return "unsupported_api_version"
    if request.answer_result_id is not None and not isinstance(request.answer_result_id, UUID):
        return "invalid_request"
    if not isinstance(request.include_rendered_citation_text, bool):
        return "invalid_request"
    return None


def map_to_response_request(request: ApiDeliveryRequest) -> ResponseRequest:
    return ResponseRequest(
        answer_request_id=request.answer_request_id,
        contract_version=API_TO_RUNTIME_CONTRACT_VERSION[request.api_contract_version],
        include_rendered_citation_text=request.include_rendered_citation_text,
        answer_result_id=request.answer_result_id,
    )


def _map_delivery_metadata(response_metadata: ResponseMetadata | None) -> ApiDeliveryMetadata | None:
    # Finding 4: null → null; object → object; never synthesize empty object
    if response_metadata is None:
        return None
    return ApiDeliveryMetadata(
        rendering_mode=response_metadata.rendering_mode,
        include_rendered_citation_text=response_metadata.include_rendered_citation_text,
        notes=response_metadata.notes,
    )


def _map_citation(citation) -> ApiDeliveryCitationReference | None:
    if citation is None:
        return None
    return ApiDeliveryCitationReference(
        citation_id=citation.citation_id,
        citation_hash=citation.citation_hash,
        rendered_citation_text=citation.rendered_citation_text,
    )


def _map_evidence_entries(package: ResponsePackage) -> list[ApiDeliveryEvidenceEntry]:
    return [
        ApiDeliveryEvidenceEntry(
            presentation_order_index=entry.presentation_order_index,
            retrieval_evidence_reference_id=entry.retrieval_evidence_reference_id,
            ranked_evidence_reference_id=entry.ranked_evidence_reference_id,
            legal_object_id=entry.legal_object_id,
            source_version_id=entry.source_version_id,
            object_identifier=entry.object_identifier,
            location_reference=entry.location_reference,
            citation_reference=_map_citation(entry.citation_reference),
            entry_metadata=entry.entry_metadata,
        )
        for entry in package.evidence_entries
    ]


def _map_uncertainty_flags(package: ResponsePackage) -> list[ApiDeliveryUncertaintyFlag]:
    return [
        ApiDeliveryUncertaintyFlag(
            flag_type=flag.flag_type,
            severity=flag.severity,
            message=flag.message,
            related_evidence_ids=list(flag.related_evidence_ids),
        )
        for flag in package.uncertainty_flags
    ]


def map_response_outcome(
    *,
    answer_request_id: UUID,
    outcome: ResponseOutcome,
) -> ApiDeliveryOutcome:
    if outcome.response_status == RESPONSE_STATUS_COMPLETED and outcome.response_package is not None:
        package = outcome.response_package
        return ApiDeliveryOutcome(
            http_status=HTTP_STATUS_SUCCESS,
            response=ApiDeliveryResponse(
                api_contract_version=CURRENT_API_CONTRACT_VERSION,
                delivery_status=DELIVERY_STATUS_COMPLETED,
                answer_request_id=package.answer_request_id,
                answer_result_id=package.answer_result_id,
                rank_count=package.rank_count,
                evidence_entries=_map_evidence_entries(package),
                uncertainty_flags=_map_uncertainty_flags(package),
                delivery_metadata=_map_delivery_metadata(package.response_metadata),
                error=None,
            ),
        )

    error_code = translate_runtime_error_category(outcome.error_category)
    return _failed_outcome(
        answer_request_id=answer_request_id,
        error_code=error_code,
        error_message=outcome.error_message,
    )


def build_api_delivery_response(
    db: Session,
    request: ApiDeliveryRequest,
) -> ApiDeliveryOutcome:
    """Single API delivery entrypoint — maps to build_response only."""
    validation_error = validate_api_delivery_request(request)
    if validation_error is not None:
        # Prefer a stable UUID when answer_request_id is invalid for envelope completeness
        anchor = request.answer_request_id if isinstance(request.answer_request_id, UUID) else UUID(int=0)
        message = None
        if validation_error == "unsupported_api_version":
            message = f"unsupported api_contract_version={request.api_contract_version!r}"
        elif validation_error == "invalid_request":
            message = "invalid ApiDeliveryRequest envelope"
        return _failed_outcome(
            answer_request_id=anchor,
            error_code=validation_error,
            error_message=message,
        )

    response_request = map_to_response_request(request)
    try:
        outcome = build_response(db, response_request)
    except ResponseRuntimeError as exc:
        error_code = translate_runtime_error_category(exc.error_category)
        return _failed_outcome(
            answer_request_id=request.answer_request_id,
            error_code=error_code,
            error_message=exc.message,
        )
    except Exception as exc:  # noqa: BLE001 — map unexpected failures to service_unavailable
        return _failed_outcome(
            answer_request_id=request.answer_request_id,
            error_code="service_unavailable",
            error_message=str(exc) or "response pipeline unavailable",
        )

    return map_response_outcome(
        answer_request_id=request.answer_request_id,
        outcome=outcome,
    )

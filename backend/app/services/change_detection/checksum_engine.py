from sqlalchemy.orm import Session

from app.core.datetime_utils import utc_now
from app.models.fetch_request import FetchRequest as FetchRequestModel
from app.models.fetch_result import FetchResult as FetchResultModel
from app.services.change_detection.engine import ChangeDetectionEngine
from app.services.change_detection.persistence import (
    ChangeDetectionPersistenceError,
    create_change_detection_request,
    persist_change_detection_result,
)
from app.services.change_detection.result import (
    ChangeDetectionEngineResult,
    ChecksumChangeDetectionRequest,
)


class ChangeDetectionEngineError(Exception):
    pass


class ChecksumChangeDetectionEngine(ChangeDetectionEngine):
    name = "checksum_change_detection_engine"
    version = "0.1.0"

    def __init__(self, *, session: Session):
        self._session = session

    def detect(self, request: ChecksumChangeDetectionRequest) -> ChangeDetectionEngineResult:
        current_result = self._session.get(FetchResultModel, request.current_fetch_result_id)
        if current_result is None:
            raise ChangeDetectionEngineError(
                f"current_fetch_result not found: {request.current_fetch_result_id}"
            )

        previous_result = None
        if request.previous_fetch_result_id is not None:
            previous_result = self._session.get(FetchResultModel, request.previous_fetch_result_id)
            if previous_result is None:
                raise ChangeDetectionEngineError(
                    f"previous_fetch_result not found: {request.previous_fetch_result_id}"
                )

        request_model = self._build_and_persist_request(
            request=request,
            current_result=current_result,
            previous_result=previous_result,
        )
        outcome = self._derive_checksum_outcome(current_result=current_result, previous_result=previous_result)

        result_model = persist_change_detection_result(
            self._session,
            change_detection_request_id=request_model.id,
            detection_status="completed",
            change_detected=outcome["change_detected"],
            change_type=outcome["change_type"],
            previous_checksum_sha256=outcome["previous_checksum_sha256"],
            current_checksum_sha256=outcome["current_checksum_sha256"],
            metadata_diff_json=None,
            structural_diff_summary=None,
            confidence=outcome["confidence"],
            review_required=outcome["review_required"],
            detector_name=self.name,
            detector_version=self.version,
            detected_at=utc_now(),
            notes=request.notes,
            error_category=outcome["error_category"],
            error_message=outcome["error_message"],
        )
        return ChangeDetectionEngineResult(
            change_detection_request_id=request_model.id,
            change_detection_result_id=result_model.id,
            change_detected=result_model.change_detected,
            change_type=result_model.change_type,
            review_required=result_model.review_required,
            confidence=result_model.confidence,
            notes=result_model.notes,
        )

    def _build_and_persist_request(
        self,
        *,
        request: ChecksumChangeDetectionRequest,
        current_result: FetchResultModel,
        previous_result: FetchResultModel | None,
    ):
        fetch_request = self._session.get(FetchRequestModel, current_result.fetch_request_id)
        monitoring_candidate_id = fetch_request.monitoring_candidate_id if fetch_request is not None else None
        previous_reference = (
            f"fetch_result:{previous_result.id}" if previous_result is not None else None
        )
        return create_change_detection_request(
            self._session,
            monitoring_candidate_id=monitoring_candidate_id,
            fetch_result_id=current_result.id,
            current_artifact_reference=f"fetch_result:{current_result.id}",
            previous_artifact_reference=previous_reference,
            requested_by_actor_type=request.requested_by_actor_type,
            requested_by_actor_identifier=request.requested_by_actor_identifier,
            detection_reason=request.detection_reason,
            notes=request.notes,
        )

    def _derive_checksum_outcome(
        self,
        *,
        current_result: FetchResultModel,
        previous_result: FetchResultModel | None,
    ) -> dict[str, str | bool | None]:
        current_checksum = current_result.checksum_sha256
        previous_checksum = previous_result.checksum_sha256 if previous_result is not None else None

        if previous_result is None:
            if current_checksum:
                return {
                    "change_detected": True,
                    "change_type": "new_artifact",
                    "review_required": True,
                    "confidence": "medium",
                    "error_category": None,
                    "error_message": None,
                    "previous_checksum_sha256": None,
                    "current_checksum_sha256": current_checksum,
                }
            return {
                "change_detected": True,
                "change_type": "unknown",
                "review_required": True,
                "confidence": "low",
                "error_category": "checksum_unavailable",
                "error_message": "current checksum is unavailable",
                "previous_checksum_sha256": None,
                "current_checksum_sha256": None,
            }

        if not current_checksum:
            return {
                "change_detected": True,
                "change_type": "unknown",
                "review_required": True,
                "confidence": "low",
                "error_category": "checksum_unavailable",
                "error_message": "current checksum is unavailable",
                "previous_checksum_sha256": previous_checksum,
                "current_checksum_sha256": None,
            }
        if not previous_checksum:
            return {
                "change_detected": True,
                "change_type": "unknown",
                "review_required": True,
                "confidence": "low",
                "error_category": "checksum_unavailable",
                "error_message": "previous checksum is unavailable",
                "previous_checksum_sha256": None,
                "current_checksum_sha256": current_checksum,
            }
        if current_checksum == previous_checksum:
            return {
                "change_detected": False,
                "change_type": "no_change",
                "review_required": False,
                "confidence": "high",
                "error_category": None,
                "error_message": None,
                "previous_checksum_sha256": previous_checksum,
                "current_checksum_sha256": current_checksum,
            }
        return {
            "change_detected": True,
            "change_type": "checksum_changed",
            "review_required": True,
            "confidence": "high",
            "error_category": None,
            "error_message": None,
            "previous_checksum_sha256": previous_checksum,
            "current_checksum_sha256": current_checksum,
        }

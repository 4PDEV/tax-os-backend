from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.datetime_utils import utc_now
from app.models.fetch_request import FetchRequest as FetchRequestModel
from app.models.fetch_result import FetchResult as FetchResultModel
from app.models.monitoring_candidate import MonitoringCandidate
from app.models.source_allowlist_entry import SourceAllowlistEntry
from app.services.fetch.contract import FetchRequest as FetchRequestContract
from app.services.fetch.result import FetchResult as FetchResultContract

REQUESTED_BY_ACTOR_TYPES = {"user", "system", "worker", "admin", "test"}
FETCH_STATUSES = {"pending", "success", "failed", "blocked", "skipped", "partial"}
FETCH_ERROR_CATEGORIES = {
    "source_unreachable",
    "access_denied",
    "robots_or_terms_restricted",
    "unsupported_content_type",
    "content_too_large",
    "checksum_failed",
    "timeout",
    "redirect_policy_failed",
    "unexpected_content",
    "unknown_failure",
}
STORAGE_BACKENDS = {"none", "database", "local_fixture", "local_test", "filesystem", "s3", "minio", "azure_blob"}


class FetchPersistenceError(Exception):
    pass


def _require_non_empty(value: str, field_name: str) -> None:
    if not value or not value.strip():
        raise FetchPersistenceError(f"{field_name} is required")


def _validate_actor_type(actor_type: str) -> None:
    if actor_type not in REQUESTED_BY_ACTOR_TYPES:
        raise FetchPersistenceError(f"invalid requested_by_actor_type: {actor_type}")


def _validate_fetch_status(fetch_status: str) -> None:
    if fetch_status not in FETCH_STATUSES:
        raise FetchPersistenceError(f"invalid fetch_status: {fetch_status}")


def _validate_error_category(error_category: str | None) -> None:
    if error_category is not None and error_category not in FETCH_ERROR_CATEGORIES:
        raise FetchPersistenceError(f"invalid error_category: {error_category}")


def _validate_storage_backend(storage_backend: str | None) -> None:
    if storage_backend is not None and storage_backend not in STORAGE_BACKENDS:
        raise FetchPersistenceError(f"invalid storage_backend: {storage_backend}")


def create_fetch_request(
    session: Session,
    *,
    requested_url: str,
    requested_by_actor_type: str,
    requested_by_actor_identifier: str | None,
    request_reason: str,
    dry_run: bool,
    local_fixture_mode: bool,
    monitoring_candidate_id: UUID | None = None,
    source_allowlist_entry_id: UUID | None = None,
    notes: str | None = None,
    requested_at: datetime | None = None,
) -> FetchRequestModel:
    _require_non_empty(requested_url, "requested_url")
    _require_non_empty(request_reason, "request_reason")
    _validate_actor_type(requested_by_actor_type)

    if monitoring_candidate_id is not None:
        candidate = session.get(MonitoringCandidate, monitoring_candidate_id)
        if candidate is None:
            raise FetchPersistenceError(f"monitoring_candidate not found: {monitoring_candidate_id}")

    if source_allowlist_entry_id is not None:
        entry = session.get(SourceAllowlistEntry, source_allowlist_entry_id)
        if entry is None:
            raise FetchPersistenceError(f"source_allowlist_entry not found: {source_allowlist_entry_id}")

    fetch_request = FetchRequestModel(
        monitoring_candidate_id=monitoring_candidate_id,
        source_allowlist_entry_id=source_allowlist_entry_id,
        requested_url=requested_url,
        requested_by_actor_type=requested_by_actor_type,
        requested_by_actor_identifier=requested_by_actor_identifier,
        request_reason=request_reason,
        requested_at=requested_at or utc_now(),
        dry_run=dry_run,
        local_fixture_mode=local_fixture_mode,
        notes=notes,
        created_at=utc_now(),
    )
    session.add(fetch_request)
    session.flush()
    return fetch_request


def persist_fetch_result(
    session: Session,
    *,
    fetch_request_id: UUID,
    fetched_url: str,
    final_url: str | None,
    fetch_status: str,
    fetched_at: datetime | None,
    http_status_code: int | None,
    content_type: str | None,
    content_length: int | None,
    checksum_sha256: str | None,
    storage_backend: str | None,
    storage_path: str | None,
    error_category: str | None,
    error_message: str | None,
    fetcher_name: str,
    fetcher_version: str,
) -> FetchResultModel:
    _require_non_empty(fetched_url, "fetched_url")
    _require_non_empty(fetcher_name, "fetcher_name")
    _require_non_empty(fetcher_version, "fetcher_version")
    _validate_fetch_status(fetch_status)
    _validate_error_category(error_category)
    _validate_storage_backend(storage_backend)

    request_record = session.get(FetchRequestModel, fetch_request_id)
    if request_record is None:
        raise FetchPersistenceError(f"fetch_request not found: {fetch_request_id}")

    fetch_result = FetchResultModel(
        fetch_request_id=fetch_request_id,
        fetched_url=fetched_url,
        final_url=final_url,
        fetch_status=fetch_status,
        fetched_at=fetched_at,
        http_status_code=http_status_code,
        content_type=content_type,
        content_length=content_length,
        checksum_sha256=checksum_sha256,
        storage_backend=storage_backend,
        storage_path=storage_path,
        error_category=error_category,
        error_message=error_message,
        fetcher_name=fetcher_name,
        fetcher_version=fetcher_version,
        created_at=utc_now(),
    )
    session.add(fetch_result)
    session.flush()
    _ = request_record
    return fetch_result


def get_fetch_request(session: Session, *, fetch_request_id: UUID) -> FetchRequestModel | None:
    return session.get(FetchRequestModel, fetch_request_id)


def list_fetch_results_for_request(session: Session, *, fetch_request_id: UUID) -> list[FetchResultModel]:
    return list(
        session.execute(
            select(FetchResultModel)
            .where(FetchResultModel.fetch_request_id == fetch_request_id)
            .order_by(FetchResultModel.created_at.asc(), FetchResultModel.id.asc())
        ).scalars()
    )


def get_latest_fetch_result_for_request(session: Session, *, fetch_request_id: UUID) -> FetchResultModel | None:
    return session.execute(
        select(FetchResultModel)
        .where(FetchResultModel.fetch_request_id == fetch_request_id)
        .order_by(FetchResultModel.created_at.desc(), FetchResultModel.id.desc())
        .limit(1)
    ).scalar_one_or_none()


def create_persisted_fetch_request_from_contract(
    session: Session,
    *,
    fetch_request: FetchRequestContract,
) -> FetchRequestModel:
    return create_fetch_request(
        session,
        requested_url=fetch_request.requested_url,
        requested_by_actor_type=fetch_request.requested_by_actor_type,
        requested_by_actor_identifier=fetch_request.requested_by_actor_identifier,
        request_reason=fetch_request.request_reason,
        dry_run=fetch_request.dry_run,
        local_fixture_mode=fetch_request.local_fixture_mode,
        monitoring_candidate_id=fetch_request.monitoring_candidate_id,
        source_allowlist_entry_id=fetch_request.source_allowlist_entry_id,
        notes=fetch_request.notes,
    )


def persist_result_from_contract(
    session: Session,
    *,
    fetch_request_id: UUID,
    fetch_result: FetchResultContract,
) -> FetchResultModel:
    return persist_fetch_result(
        session,
        fetch_request_id=fetch_request_id,
        fetched_url=fetch_result.fetched_url,
        final_url=fetch_result.final_url,
        fetch_status=fetch_result.fetch_status,
        fetched_at=fetch_result.fetched_at,
        http_status_code=fetch_result.http_status_code,
        content_type=fetch_result.content_type,
        content_length=fetch_result.content_length,
        checksum_sha256=fetch_result.checksum_sha256,
        storage_backend=fetch_result.storage_backend,
        storage_path=fetch_result.storage_path,
        error_category=fetch_result.error_category,
        error_message=fetch_result.error_message,
        fetcher_name=fetch_result.fetcher_name,
        fetcher_version=fetch_result.fetcher_version,
    )

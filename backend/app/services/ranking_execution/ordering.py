from datetime import date

from app.services.ranking_execution.models import RankingEvidenceRow


def _asc_nulls_last_date(value: date | None) -> tuple:
    if value is None:
        return (1, date.min)
    return (0, value)


def _desc_nulls_last_date(value: date | None) -> tuple:
    if value is None:
        return (1, 0)
    return (0, -value.toordinal())


def _asc_nulls_last_str(value: str | None) -> tuple:
    if value is None:
        return (1, "")
    return (0, value)


def _asc_nulls_last_uuid(value) -> tuple:
    return (0, str(value))


def _within_group_key(row: RankingEvidenceRow) -> tuple:
    return (
        _asc_nulls_last_date(row.effective_from),
        row.legal_object_id,
        _asc_nulls_last_uuid(row.legal_object_version_id),
        _asc_nulls_last_str(row.citation_hash),
        _asc_nulls_last_str(row.object_identifier),
        _asc_nulls_last_uuid(row.retrieval_evidence_reference_id),
    )


def _effective_date_desc_key(row: RankingEvidenceRow) -> tuple:
    return (
        _desc_nulls_last_date(row.effective_from),
        row.legal_object_id,
        _asc_nulls_last_uuid(row.legal_object_version_id),
        _asc_nulls_last_str(row.citation_hash),
        _asc_nulls_last_str(row.object_identifier),
        _asc_nulls_last_uuid(row.retrieval_evidence_reference_id),
    )


def sort_canonical(rows: list[RankingEvidenceRow]) -> list[RankingEvidenceRow]:
    return sorted(rows, key=lambda row: row.deterministic_order_index)


def sort_effective_date_desc(rows: list[RankingEvidenceRow]) -> list[RankingEvidenceRow]:
    return sorted(rows, key=_effective_date_desc_key)


def sort_group_by_source(rows: list[RankingEvidenceRow]) -> list[RankingEvidenceRow]:
    return sorted(
        rows,
        key=lambda row: (
            _asc_nulls_last_uuid(row.source_version_id),
            *_within_group_key(row),
        ),
    )


def _asc_nulls_last_uuid_optional(value) -> tuple:
    if value is None:
        return (1, "")
    return (0, str(value))


def sort_group_by_document(rows: list[RankingEvidenceRow]) -> list[RankingEvidenceRow]:
    return sorted(
        rows,
        key=lambda row: (
            _asc_nulls_last_uuid_optional(row.source_document_id),
            *_within_group_key(row),
        ),
    )


def apply_ranking_profile(
    rows: list[RankingEvidenceRow],
    *,
    ranking_profile: str,
) -> list[RankingEvidenceRow]:
    if ranking_profile == "CANONICAL":
        return sort_canonical(rows)
    if ranking_profile == "EFFECTIVE_DATE_DESC":
        return sort_effective_date_desc(rows)
    if ranking_profile == "GROUP_BY_SOURCE":
        return sort_group_by_source(rows)
    if ranking_profile == "GROUP_BY_DOCUMENT":
        return sort_group_by_document(rows)
    raise ValueError(f"invalid ranking_profile: {ranking_profile}")

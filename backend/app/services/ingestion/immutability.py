from app.services.ingestion.errors import IngestionImmutabilityError

IMMUTABLE_EXTRACTED_TEXT_FIELDS = frozenset(
    {
        "extraction_run_id",
        "source_version_id",
        "content_hash",
        "raw_text",
        "normalized_text",
        "storage_backend",
        "created_at",
    }
)

IMMUTABLE_PARSED_STRUCTURE_FIELDS = frozenset(
    {
        "parser_run_id",
        "source_version_id",
        "structure_type",
        "structure_json",
        "structure_hash",
        "created_at",
    }
)


def assert_extracted_text_immutable(*, field_name: str) -> None:
    if field_name in IMMUTABLE_EXTRACTED_TEXT_FIELDS:
        raise IngestionImmutabilityError(
            f"extracted_texts.{field_name} is immutable after creation"
        )


def assert_parsed_structure_immutable(*, field_name: str) -> None:
    if field_name in IMMUTABLE_PARSED_STRUCTURE_FIELDS:
        raise IngestionImmutabilityError(
            f"parsed_structures.{field_name} is immutable after creation"
        )


def assert_hard_delete_prohibited(entity_label: str) -> None:
    raise IngestionImmutabilityError(f"hard delete of {entity_label} is prohibited")
